/**
 * Tempo Mode System Foundation
 * Centralized UX State Controller for Tempo's 4 Modes:
 * - default (Dmode): Neutral, exploratory Tempo experience
 * - emergency (Emode): Acute academic deadline triage & high-direction execution
 * - recovery (Rmode): Nervous system decompression & sustainable rhythm rebuild
 * - unclear (Umode): Guided unpack & reflective clarity
 * 
 * Core Design Principle:
 * "A Tempo Mode does not decide what the user is allowed to do.
 * It decides what Tempo brings forward first."
 * 
 * Existing plans/tasks are reusable across modes.
 * Mode switches never delete, duplicate, or silo task data.
 */

window.TempoMode = (function() {
    const MODES = {
        DEFAULT: 'default',
        EMERGENCY: 'emergency',
        RECOVERY: 'recovery',
        UNCLEAR: 'unclear'
    };

    const EPLAN_STATES = {
        NO_PLAN: 'PLAN_NO_PLAN',
        INCOMPLETE: 'PLAN_INCOMPLETE',
        ACTIVE_TODAY: 'PLAN_ACTIVE_TODAY',
        TODAY_COMPLETE: 'PLAN_TODAY_COMPLETE',
        NO_WORK_TODAY: 'PLAN_NO_WORK_TODAY',
        TIME_ENDED_INCOMPLETE: 'PLAN_TIME_ENDED_INCOMPLETE',
        STALE: 'PLAN_STALE',
        COMPLETE: 'PLAN_COMPLETE'
    };

    // Central active context: exactly null (Entry Home) | MODES.EMERGENCY | MODES.RECOVERY
    let activeContext = null;

    // Active shared assessment/tool session (e.g. 'ucheck')
    let activeSharedTool = null;

    function isViLocale() {
        return !window.TempoI18n || typeof window.TempoI18n.getLanguage !== 'function' || window.TempoI18n.getLanguage() === 'vi';
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

    function isMissedSchedulePromptDismissed(taskId, currentScheduledDate) {
        if (!taskId) return false;
        if (sessionFlags && sessionFlags.dismissedMissedScheduleTasks && sessionFlags.dismissedMissedScheduleTasks.has(String(taskId))) {
            return true;
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
        if (!sessionFlags.dismissedMissedScheduleTasks) {
            sessionFlags.dismissedMissedScheduleTasks = new Set();
        }
        sessionFlags.dismissedMissedScheduleTasks.add(String(taskId));
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
        if (sessionFlags && sessionFlags.dismissedMissedScheduleTasks) {
            sessionFlags.dismissedMissedScheduleTasks.delete(String(taskId));
        }
        try {
            const stored = JSON.parse(localStorage.getItem('tempo_dismissed_missed_schedule') || '{}');
            delete stored[String(taskId)];
            localStorage.setItem('tempo_dismissed_missed_schedule', JSON.stringify(stored));
        } catch (e) {}
    }

    // Source context for shared assessment / tools: 'entry' | 'emergency' | 'recovery'
    let sourceContext = 'entry';

    // Central pending intent across auth gate: null | { type: 'mode'|'tool', destination: string, tool?: string, sourceContext?: string }
    let pendingIntent = null;

    // Session-level flags to prevent repeating dismissed alerts
    let sessionFlags = {
        dismissedStaleWarning: false,
        dismissedTimeEndedToday: false,
        viewingTomorrowTask: false,
        restingForToday: false,
        dismissedMissedScheduleTasks: new Set()
    };

    let currentActiveHomeState = null;

    // Expanded task cards on Default Home
    let dmodeExpandedTaskIds = new Set();

    /**
     * Resolves the user's persisted active context from localStorage.
     * Checks account-isolated storage first, then global fallback.
     */
    function getUserPersistedActiveContext(specificUid) {
        try {
            const uid = specificUid || (window.TempoAuth && typeof window.TempoAuth.getCurrentUserId === 'function' ? window.TempoAuth.getCurrentUserId() : null);
            if (uid) {
                const userSaved = localStorage.getItem('tempo_user_established_context_' + uid);
                if (userSaved === MODES.EMERGENCY || userSaved === MODES.RECOVERY || userSaved === MODES.UNCLEAR) {
                    return userSaved;
                }
                if (userSaved === MODES.DEFAULT) {
                    return MODES.DEFAULT;
                }
            }

            const savedEstablished = localStorage.getItem('tempo_established_context');
            if (savedEstablished === MODES.EMERGENCY || savedEstablished === MODES.RECOVERY || savedEstablished === MODES.UNCLEAR) {
                return savedEstablished;
            }
            if (savedEstablished === MODES.DEFAULT) {
                return MODES.DEFAULT;
            }

            const savedMode = localStorage.getItem('tempo_current_mode');
            if (savedMode === MODES.EMERGENCY || savedMode === MODES.RECOVERY || savedMode === MODES.UNCLEAR) {
                return savedMode;
            }
        } catch (e) {}

        return null;
    }

    function hasEstablishedContext() {
        const ctx = getUserPersistedActiveContext();
        return ctx === MODES.EMERGENCY || ctx === MODES.RECOVERY;
    }

    function init() {
        // Load persisted context safely from localStorage
        try {
            const authState = window.TempoAuth && typeof window.TempoAuth.getAuthState === 'function'
                ? window.TempoAuth.getAuthState()
                : 'AUTH_LOADING';
            const isAuthenticated = window.TempoAuth && !!window.TempoAuth.getCurrentUser();
            const uid = window.TempoAuth && typeof window.TempoAuth.getCurrentUserId === 'function' ? window.TempoAuth.getCurrentUserId() : null;

            const userEstablished = uid ? localStorage.getItem('tempo_user_established_context_' + uid) : null;
            const globalEstablished = localStorage.getItem('tempo_established_context');
            const savedMode = localStorage.getItem('tempo_current_mode');

            activeSharedTool = null;
            try {
                const savedTool = sessionStorage.getItem('tempo_active_shared_tool');
                if (savedTool === 'ucheck') {
                    activeSharedTool = 'ucheck';
        try {
            sessionStorage.setItem('tempo_active_shared_tool', 'ucheck');
        } catch (e) {}
                }
            } catch (e) {}

            if (authState === 'AUTH_LOADING') {
                if (savedMode === MODES.EMERGENCY || savedMode === MODES.RECOVERY) {
                    activeContext = savedMode;
                    sourceContext = savedMode;
                } else if (savedMode === MODES.UNCLEAR) {
                    activeContext = null;
                    sourceContext = getOriginatingMode() || 'entry';
                    activeSharedTool = 'ucheck';
                } else {
                    activeContext = null;
                    sourceContext = 'entry';
                }
            } else if (!isAuthenticated) {
                // Anonymous user -> Always Entry Home (activeContext = null)
                activeContext = null;
                sourceContext = 'entry';
                localStorage.setItem('tempo_current_mode', MODES.DEFAULT);
            } else {
                // Authenticated user: restore their established context or default to Entry Home
                const established = getUserPersistedActiveContext(uid);
                if (established === MODES.EMERGENCY) {
                    activeContext = MODES.EMERGENCY;
                    sourceContext = 'emergency';
                } else if (established === MODES.RECOVERY) {
                    activeContext = MODES.RECOVERY;
                    sourceContext = 'recovery';
                } else if (established === MODES.UNCLEAR || savedMode === MODES.UNCLEAR) {
                    activeContext = null;
                    sourceContext = getOriginatingMode() || 'entry';
                    activeSharedTool = 'ucheck';
                } else {
                    // Authenticated user with no established active context -> Entry Home
                    activeContext = null;
                    sourceContext = 'entry';
                    localStorage.setItem('tempo_current_mode', MODES.DEFAULT);
                }
            }

            const savedOrigin = getOriginatingMode();
            if (savedOrigin && (activeContext === MODES.UNCLEAR || activeSharedTool === 'ucheck')) {
                sourceContext = savedOrigin;
            }

            const savedPendingIntent = localStorage.getItem('tempo_pending_intent');
            if (savedPendingIntent) {
                try { pendingIntent = JSON.parse(savedPendingIntent); } catch (e) {}
            }
            if (!pendingIntent) {
                const savedPending = localStorage.getItem('tempo_pending_mode');
                if (savedPending && Object.values(MODES).includes(savedPending)) {
                    pendingIntent = { type: 'mode', destination: savedPending };
                }
            }
        } catch (e) {
            console.warn("[TempoMode] localStorage access error:", e);
        }

        renderShellIndicator();
        bindEvents();

        // Synchronize active mode dashboard with strict mutual exclusivity
        renderActiveModeHome();

        if (activeContext === MODES.RECOVERY && activeSharedTool !== 'ucheck') {
            if (window.TempoRecoverySetup && typeof window.TempoRecoverySetup.handleRmodeEntry === 'function') {
                window.TempoRecoverySetup.handleRmodeEntry();
            } else if (window.TempoRecoverySetup && typeof window.TempoRecoverySetup.shouldShowFirstTimeWelcome === 'function') {
                if (window.TempoRecoverySetup.shouldShowFirstTimeWelcome()) {
                    window.TempoRecoverySetup.open(1);
                }
            }
        }
    }

    function bindEvents() {
        // Close change mode modal on backdrop click or escape key
        const changeModeModal = document.getElementById('modal-change-mode');
        if (changeModeModal) {
            changeModeModal.addEventListener('click', (e) => {
                if (e.target === changeModeModal) {
                    closeChangeModeModal();
                }
            });
        }

        // Rerender active mode dashboard when language changes
        if (window.TempoI18n && typeof window.TempoI18n.onLanguageChange === 'function') {
            window.TempoI18n.onLanguageChange(() => {
                renderActiveModeHome();
                const stressCheckScreen = document.getElementById('screen-stress-check');
                if (stressCheckScreen && !stressCheckScreen.classList.contains('hidden')) {
                    if (window.TempoSelfCheckWorkspace && typeof window.TempoSelfCheckWorkspace.render === 'function') {
                        window.TempoSelfCheckWorkspace.render();
                    }
                }
            });
        }

        // Close mode selector dropdown on outside click
        document.addEventListener('click', (e) => {
            if (!e.target.closest('#home-mode-selector-wrapper, [id^="home-mode-selector-wrapper"]') && !e.target.closest('#mode-indicator-shell')) {
                closeAllModeDropdowns();
            }
        });

        // Close on Escape key
        window.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                closeAllModeDropdowns();
                if (changeModeModal && !changeModeModal.classList.contains('hidden')) {
                    closeChangeModeModal();
                }
            }
        });
    }

    function getActiveContext() {
        return activeContext;
    }

    function hasActiveContext() {
        return activeContext !== null;
    }

    const UCHECK_ORIGIN_STORAGE_KEY = 'tempo_ucheck_originating_mode';

    function setOriginatingMode(originMode) {
        let normalized = null;
        if (originMode === MODES.RECOVERY || originMode === 'recovery') {
            normalized = 'recovery';
        } else if (originMode === MODES.EMERGENCY || originMode === 'emergency' || originMode === 'urgent') {
            normalized = 'emergency';
        } else if (originMode === 'entry' || originMode === 'default' || originMode === MODES.DEFAULT) {
            normalized = 'entry';
        }
        if (normalized) {
            sourceContext = normalized;
            try {
                sessionStorage.setItem(UCHECK_ORIGIN_STORAGE_KEY, normalized);
                localStorage.setItem(UCHECK_ORIGIN_STORAGE_KEY, normalized);
            } catch (e) {}
        }
    }

    function getOriginatingMode() {
        let origin = null;
        try {
            origin = sessionStorage.getItem(UCHECK_ORIGIN_STORAGE_KEY) || localStorage.getItem(UCHECK_ORIGIN_STORAGE_KEY);
        } catch (e) {}
        if (!origin || origin === 'unclear') {
            if (sourceContext && sourceContext !== 'unclear') {
                origin = sourceContext;
            }
        }
        if (origin === 'urgent') origin = 'emergency';
        return (origin === 'recovery' || origin === 'emergency' || origin === 'entry') ? origin : null;
    }

    function clearOriginatingMode() {
        try {
            sessionStorage.removeItem(UCHECK_ORIGIN_STORAGE_KEY);
            localStorage.removeItem(UCHECK_ORIGIN_STORAGE_KEY);
        } catch (e) {}
    }

    function getSourceContext() {
        return sourceContext;
    }

    function setSourceContext(ctx) {
        if (ctx === 'emergency' || ctx === 'recovery' || ctx === 'entry') {
            sourceContext = ctx;
            setOriginatingMode(ctx);
        } else {
            sourceContext = 'entry';
        }
    }

    function getActiveSharedTool() {
        if (!activeSharedTool) {
            try {
                const saved = sessionStorage.getItem('tempo_active_shared_tool');
                if (saved === 'ucheck') {
                    activeSharedTool = 'ucheck';
                    return 'ucheck';
                }
            } catch (e) {}
        }
        return activeSharedTool;
    }

    function isValidPendingIntent(intent) {
        if (!intent || typeof intent !== 'object') return false;
        const dest = (intent.destination || intent.tool || '').toLowerCase();
        const validDests = [
            MODES.EMERGENCY, MODES.RECOVERY, 'emergency', 'recovery', 'urgent', 'urmode', 'rmode',
            'ucheck', 'unclear', 'unclear-mode',
            'strack',
            'plan-workspace', 'stress-check', 'routine', 'today', 'personal-space', 'posts', 'direct-messages'
        ];
        if (!validDests.includes(dest)) return false;

        const act = (intent.action || 'navigate').toLowerCase();
        const validActions = ['select', 'open', 'navigate', 'resume', 'setup', 'checkin', 'manage', 'history', 'view', 'edit'];
        if (!validActions.includes(act)) return false;

        return true;
    }

    function getPendingIntent() {
        return pendingIntent;
    }

    function setPendingIntent(intent) {
        if (!intent) {
            clearPendingIntent();
            return;
        }

        const dest = intent.destination || intent.tool || (intent.type === 'mode' ? intent.destination : null);
        let act = intent.action;
        if (!act) {
            if (intent.type === 'mode' || dest === MODES.EMERGENCY || dest === MODES.RECOVERY || dest === 'urgent' || dest === 'urmode' || dest === 'rmode') {
                act = 'select';
            } else if (intent.type === 'ucheck' || dest === 'ucheck') {
                act = 'open';
            } else {
                act = 'navigate';
            }
        }
        const src = intent.source || intent.sourceContext || 'entry';
        const params = intent.requiredParams || intent.options || {};

        // Invariant 18A & 18E: Prevent duplicate or stacked intent if identical
        if (pendingIntent && 
            (pendingIntent.destination === dest || pendingIntent.tool === dest) && 
            pendingIntent.action === act) {
            return;
        }

        const normalized = {
            destination: dest,
            action: act,
            source: src,
            requiredParams: params,
            // Backwards-compatible legacy properties
            type: intent.type || (dest === MODES.EMERGENCY || dest === MODES.RECOVERY || dest === 'urgent' || dest === 'urmode' || dest === 'rmode' ? 'mode' : (dest === 'ucheck' ? 'ucheck' : 'tool')),
            sourceContext: src,
            options: params,
            tool: dest
        };

        pendingIntent = normalized;
        try {
            localStorage.setItem('tempo_pending_intent', JSON.stringify(normalized));
            if (normalized.type === 'mode' || normalized.destination === MODES.EMERGENCY || normalized.destination === MODES.RECOVERY) {
                localStorage.setItem('tempo_pending_mode', normalized.destination);
            }
        } catch (e) {}
    }

    function clearPendingIntent() {
        pendingIntent = null;
        try {
            localStorage.removeItem('tempo_pending_intent');
            localStorage.removeItem('tempo_pending_mode');
        } catch (e) {}
    }

    function isUCheckActiveView() {
        if (activeSharedTool === 'ucheck') return true;
        if (activeContext === MODES.UNCLEAR) return true;
        try {
            if (sessionStorage.getItem('tempo_active_shared_tool') === 'ucheck') return true;
        } catch (e) {}
        const umodeBox = document.getElementById('umode-home-content');
        if (umodeBox && !umodeBox.classList.contains('hidden')) return true;
        const screenExplore = document.getElementById('screen-explore-mental-health-tests');
        if (screenExplore && !screenExplore.classList.contains('hidden')) return true;
        const screenResults = document.getElementById('screen-my-test-results');
        if (screenResults && !screenResults.classList.contains('hidden')) return true;
        const screenUnclear = document.getElementById('screen-unclear-mode');
        if (screenUnclear && !screenUnclear.classList.contains('hidden')) return true;
        const hash = window.location.hash || '';
        if (hash === '#ucheck' || hash.startsWith('#ucheck?') ||
            hash === '#unclear' || hash.startsWith('#unclear?') ||
            hash === '#unclear-mode' || hash.startsWith('#unclear-mode?') ||
            hash === '#explore-mental-health-tests' || hash.startsWith('#explore-mental-health-tests?') ||
            hash === '#mental-health-tests' || hash.startsWith('#mental-health-tests?') ||
            hash === '#my-test-results' || hash.startsWith('#my-test-results?') ||
            hash === '#phq9' || hash.startsWith('#phq9?') ||
            hash === '#gad7' || hash.startsWith('#gad7?') ||
            hash === '#cesd' || hash.startsWith('#cesd?') ||
            hash === '#pas' || hash.startsWith('#pas?')) {
            return true;
        }
        return false;
    }

    function getMode() {
        if (isUCheckActiveView()) return MODES.UNCLEAR;
        if (activeContext === MODES.EMERGENCY) return MODES.EMERGENCY;
        if (activeContext === MODES.RECOVERY) return MODES.RECOVERY;
        if (activeContext === MODES.UNCLEAR) return MODES.UNCLEAR;
        return MODES.DEFAULT;
    }

    function getPendingMode() {
        if (pendingIntent && pendingIntent.type === 'mode') {
            return pendingIntent.destination;
        }
        return null;
    }

    function hasPendingMode() {
        return pendingIntent !== null;
    }

    function hasPendingIntent() {
        return pendingIntent !== null;
    }

    function getModeDisplayName(mode) {
        if (window.t) {
            switch (mode) {
                case MODES.EMERGENCY: return window.t('modes.urgent.name', {}, 'Urgent Mode');
                case MODES.RECOVERY: return window.t('modes.recovery.name', {}, 'Recovery Mode');
                case MODES.UNCLEAR: return window.t('modes.unclear.name', {}, 'Unclear Mode');
                default: return window.t('modes.default.name', {}, 'Default Tempo');
            }
        }
        switch (mode) {
            case MODES.EMERGENCY: return 'Urgent Mode';
            case MODES.RECOVERY: return 'Recovery Mode';
            case MODES.UNCLEAR: return 'Unclear Mode';
            default: return 'Default Tempo';
        }
    }

    /**
     * Central active context transition controller.
     * Transitions activeContext only between: null, 'emergency', and 'recovery'.
     */
    function transitionContext(targetContext, options = {}) {
        if (targetContext === 'urgent') targetContext = MODES.EMERGENCY;
        if (targetContext === 'default') targetContext = null;
        if (targetContext === MODES.UNCLEAR) {
            // Unclear Mode is a TOOL (Ucheck), NOT an Active Context (Mode).
            // Preserve the user's activeContext (Rmode, Urgent Mode, or Default).
            const origin = options.sourceContext || (activeContext === MODES.EMERGENCY ? 'emergency' : (activeContext === MODES.RECOVERY ? 'recovery' : (getOriginatingMode() || 'entry')));
            openUcheck(Object.assign({}, options, { sourceContext: origin }));
            return;
        }
        if (targetContext !== MODES.EMERGENCY && targetContext !== MODES.RECOVERY) {
            targetContext = null;
        }

        const prevContext = activeContext;
        activeContext = targetContext;
        activeSharedTool = null;
        try {
            sessionStorage.removeItem('tempo_active_shared_tool');
        } catch (e) {}

        sourceContext = targetContext === MODES.EMERGENCY ? 'emergency' : (targetContext === MODES.RECOVERY ? 'recovery' : 'entry');
        clearOriginatingMode();

        clearPendingIntent();

        try {
            const uid = window.TempoAuth && typeof window.TempoAuth.getCurrentUserId === 'function' ? window.TempoAuth.getCurrentUserId() : null;
            if (targetContext) {
                localStorage.setItem('tempo_established_context', targetContext);
                localStorage.setItem('tempo_current_mode', targetContext);
                if (uid) {
                    localStorage.setItem('tempo_user_established_context_' + uid, targetContext);
                }
            } else {
                localStorage.setItem('tempo_established_context', MODES.DEFAULT);
                localStorage.setItem('tempo_current_mode', MODES.DEFAULT);
                if (uid && !options.preserveUserEstablishedContext) {
                    localStorage.setItem('tempo_user_established_context_' + uid, MODES.DEFAULT);
                }
            }
        } catch (e) {}

        renderShellIndicator();
        closeChangeModeModal();
        closeAllModeDropdowns();

        // Only clear the Rmode session welcomed guard if the user explicitly switches away from Rmode to another mode
        if (targetContext !== MODES.RECOVERY && targetContext !== null && prevContext === MODES.RECOVERY) {
            try {
                const uid = (window.TempoAuth && typeof window.TempoAuth.getCurrentUserId === 'function') ? (window.TempoAuth.getCurrentUserId() || 'local_user') : 'local_user';
                sessionStorage.removeItem(`tempo_rmode_session_welcomed_${uid}`);
            } catch (e) {}
        }

        if (!options.silent && window.TempoApp) {
            if (targetContext === MODES.EMERGENCY) {
                window.TempoApp.showToast("⚡ Urgent Mode active");
            } else if (targetContext === MODES.RECOVERY) {
                window.TempoApp.showToast("🌱 Switched to Recovery Mode");
            } else {
                window.TempoApp.showToast("Returned to Entry Home. All tasks remain saved.");
            }
        }

        // Synchronize view for active mode dashboard with strict mutual exclusivity
        renderActiveModeHome();

        if (!options.silent && window.TempoApp) {
            window.TempoApp.navigateTo('today');
        }

        if (targetContext === MODES.RECOVERY) {
            const isSwitchingIntoRmode = (prevContext !== MODES.RECOVERY);
            if (isSwitchingIntoRmode && !options.skipSetupCheck) {
                if (window.TempoRecoverySetup && typeof window.TempoRecoverySetup.handleRmodeEntry === 'function') {
                    window.TempoRecoverySetup.handleRmodeEntry(options);
                } else if (window.TempoRecoverySetup && typeof window.TempoRecoverySetup.shouldShowFirstTimeWelcome === 'function') {
                    if (window.TempoRecoverySetup.shouldShowFirstTimeWelcome()) {
                        window.TempoRecoverySetup.open(1);
                    }
                }
            }
        }
    }

    /**
     * Request entry into an active context.
     * Enforces auth gate for guest users while keeping Entry Home completely open.
     */
    function requestContext(targetContext, origin = 'entry') {
        if (targetContext === 'urgent') targetContext = MODES.EMERGENCY;
        if (targetContext === 'default') targetContext = null;
        if (targetContext !== MODES.EMERGENCY && targetContext !== MODES.RECOVERY) {
            transitionContext(null);
            return;
        }

        const isAuthenticated = window.TempoAuth && !!window.TempoAuth.getCurrentUser();

        if (isAuthenticated) {
            transitionContext(targetContext);
            if (targetContext === MODES.EMERGENCY) {
                if (origin === 'entry' || origin === 'selector') {
                    if (window.TempoUrmodeFlow && typeof window.TempoUrmodeFlow.queueResetPopup === 'function') {
                        window.TempoUrmodeFlow.queueResetPopup();
                    }
                }
                if (window.TempoApp) window.TempoApp.navigateTo('today');
            } else if (targetContext === MODES.RECOVERY) {
                if (window.TempoApp) window.TempoApp.navigateTo('today');
            }
        } else {
            // Guest user: save pending intent, show auth gate, do NOT activate context yet
            setPendingIntent({
                destination: targetContext,
                action: 'select',
                source: origin || sourceContext || 'entry',
                requiredParams: {},
                type: 'mode',
                sourceContext: origin || sourceContext || 'entry'
            });

            updateAuthGateBanners(targetContext);

            if (window.TempoAuth) {
                window.TempoAuth.openSignInModal();
            }

            if (window.TempoApp) {
                window.TempoApp.showToast(`Sign in or create a free account to enter ${getModeDisplayName(targetContext)}.`);
            }
        }
    }

    /**
     * Opens Ucheck shared assessment flow without mutating activeContext.
     * Preserves sourceContext so exit returns exactly to origin.
     * Enforces authentication boundary for guest users.
     */
    function openUcheck(options = {}) {
        const src = options.sourceContext || (activeContext === MODES.EMERGENCY ? 'emergency' : (activeContext === MODES.RECOVERY ? 'recovery' : (getOriginatingMode() || 'entry')));
        sourceContext = src;
        setOriginatingMode(src);

        const isAuthenticated = window.TempoAuth && !!window.TempoAuth.getCurrentUser();

        if (!isAuthenticated) {
            // Guest user: save pending intent for Ucheck, show auth gate, do NOT open Ucheck yet
            setPendingIntent({
                destination: 'ucheck',
                action: 'open',
                source: src,
                requiredParams: options,
                type: 'ucheck',
                options: options,
                sourceContext: src
            });

            closeChangeModeModal();
            closeAllModeDropdowns();

            updateAuthGateBanners(MODES.UNCLEAR);

            if (window.TempoAuth && typeof window.TempoAuth.openSignInModal === 'function') {
                window.TempoAuth.openSignInModal();
            }

            if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                window.TempoApp.showToast("Please sign in or create an account to access Unclear Mode assessment.");
            }
            return;
        }

        activeSharedTool = 'ucheck';
        try {
            sessionStorage.setItem('tempo_active_shared_tool', 'ucheck');
        } catch (e) {}

        renderShellIndicator();
        closeChangeModeModal();
        closeAllModeDropdowns();

        applyModeVisibility(MODES.UNCLEAR);

        if (window.TempoUnclearMode) {
            if (options.startNew) {
                window.TempoUnclearMode.startNewCheckIn();
            } else if (options.resumeDraftId) {
                window.TempoUnclearMode.resumeDraft(options.resumeDraftId);
            } else if (options.adjustVersionId) {
                window.TempoUnclearMode.adjustCompletedCheckIn(options.adjustVersionId);
            } else {
                window.TempoUnclearMode.renderHome();
            }
        }

        if (window.TempoApp) {
            window.TempoApp.navigateTo('today');
        }
    }

    function isUserAuthenticated() {
        return Boolean(
            window.TempoAuth && 
            typeof window.TempoAuth.getCurrentUser === 'function' && 
            window.TempoAuth.getCurrentUser() &&
            (typeof window.TempoAuth.getAuthState !== 'function' || window.TempoAuth.getAuthState() === 'authenticated') &&
            !(typeof window.TempoAuth.isRegistrationInProgress === 'function' && window.TempoAuth.isRegistrationInProgress())
        );
    }

    /**
     * Opens Strack (UI display label: "Self-check") shared recovery tracking tool.
     * Enforces authentication boundary for guest users.
     * Stable internal destination identifier is strictly 'strack'.
     * Decoupled from Rmode: Strack is a tool, not an active context.
     */
    function openStrack(action = 'open', options = {}) {
        if (typeof action === 'object' && action !== null && Object.keys(options || {}).length === 0) {
            options = action;
            action = options.action || 'open';
        }

        const isAuthenticated = isUserAuthenticated();
        const persistedCtx = isAuthenticated ? getUserPersistedActiveContext() : null;

        let src;
        if (options && options.sourceContext && options.sourceContext !== 'entry') {
            src = options.sourceContext;
        } else if (persistedCtx === MODES.RECOVERY || activeContext === MODES.RECOVERY) {
            src = 'recovery';
        } else if (persistedCtx === MODES.EMERGENCY || activeContext === MODES.EMERGENCY) {
            src = 'emergency';
        } else if (persistedCtx === MODES.UNCLEAR || activeContext === MODES.UNCLEAR) {
            src = 'unclear';
        } else if (options && options.sourceContext) {
            src = options.sourceContext;
        } else {
            src = 'entry';
        }
        sourceContext = src;
        setOriginatingMode(src);

        const returnLabelEl = document.getElementById('stress-check-return-text');
        if (returnLabelEl) {
            if (src === 'recovery') returnLabelEl.textContent = 'Return to Recovery Mode';
            else if (src === 'emergency') returnLabelEl.textContent = 'Return to Urgent Mode';
            else if (src === 'unclear') returnLabelEl.textContent = 'Return to Unclear Mode';
            else returnLabelEl.textContent = 'Return Home';
        }

        if (!isAuthenticated) {
            // Guest user: save pending intent for Strack, show auth gate, do NOT open Strack yet
            setPendingIntent({
                destination: 'strack',
                action: action || 'open',
                source: src,
                sourceContext: src,
                requiredParams: options || {},
                type: 'tool',
                tool: 'strack'
            });

            closeChangeModeModal();
            closeAllModeDropdowns();

            if (window.TempoRecoverySetup && typeof window.TempoRecoverySetup.close === 'function') {
                window.TempoRecoverySetup.close();
            }
            if (window.TempoRecoverySelfCheck) {
                if (typeof window.TempoRecoverySelfCheck.closeManage === 'function') window.TempoRecoverySelfCheck.closeManage();
                if (typeof window.TempoRecoverySelfCheck.closeDailyCheckin === 'function') window.TempoRecoverySelfCheck.closeDailyCheckin();
                if (typeof window.TempoRecoverySelfCheck.closeTrackerModal === 'function') window.TempoRecoverySelfCheck.closeTrackerModal();
                if (typeof window.TempoRecoverySelfCheck.closeViewToday === 'function') window.TempoRecoverySelfCheck.closeViewToday();
            }

            if (window.TempoAuth && typeof window.TempoAuth.openSignInModal === 'function') {
                window.TempoAuth.openSignInModal();
            }

            if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                window.TempoApp.showToast("Please sign in or create an account to access Self-check.");
            }
            return;
        }

        // Authenticated user: open Strack directly without Auth Gate
        activeSharedTool = 'strack';
        executeStrackAction(action, options);
    }

    function showStressCheckScreen() {
        const isAuthenticated = isUserAuthenticated();
        if (!isAuthenticated) {
            console.warn("[TempoMode] Protected route access blocked: Strack requires authentication.");
            openStrack('tool', { view: 'page' });
            return;
        }

        activeSharedTool = 'strack';
        const persisted = getUserPersistedActiveContext();
        if (persisted === MODES.RECOVERY || activeContext === MODES.RECOVERY) {
            sourceContext = 'recovery';
        } else if (persisted === MODES.EMERGENCY || activeContext === MODES.EMERGENCY) {
            sourceContext = 'emergency';
        } else if (persisted === MODES.UNCLEAR || activeContext === MODES.UNCLEAR) {
            sourceContext = 'unclear';
        } else if (!sourceContext || sourceContext === 'entry') {
            sourceContext = getOriginatingMode() || 'entry';
        }
        setOriginatingMode(sourceContext);

        const scReturnLabel = document.getElementById('stress-check-return-text');
        if (scReturnLabel) {
            if (sourceContext === 'recovery') scReturnLabel.textContent = 'Return to Recovery Mode';
            else if (sourceContext === 'emergency') scReturnLabel.textContent = 'Return to Urgent Mode';
            else if (sourceContext === 'unclear') scReturnLabel.textContent = 'Return to Unclear Mode';
            else scReturnLabel.textContent = 'Return Home';
        }
        const scHomeText = document.getElementById('selfcheck-return-home-text');
        if (scHomeText) {
            const isVi = (window.TempoI18n && typeof window.TempoI18n.getLanguage === 'function') ? (window.TempoI18n.getLanguage() === 'vi') : false;
            if (sourceContext === 'recovery') scHomeText.textContent = isVi ? (window.t ? window.t('selfCheckWorkspace.returnRecovery', {}, 'Quay lại Dashboard') : 'Quay lại Dashboard') : 'Return to Recovery Mode';
            else if (sourceContext === 'emergency') scHomeText.textContent = isVi ? (window.t ? window.t('selfCheckWorkspace.returnUrgent', {}, 'Quay lại Chế độ khẩn cấp') : 'Quay lại Chế độ khẩn cấp') : 'Return to Urgent Mode';
            else if (sourceContext === 'unclear') scHomeText.textContent = isVi ? (window.t ? window.t('selfCheckWorkspace.returnUnclear', {}, 'Quay lại Chế độ mơ hồ') : 'Quay lại Chế độ mơ hồ') : 'Return to Unclear Mode';
            else scHomeText.textContent = isVi ? (window.t ? window.t('selfCheckWorkspace.returnHome', {}, 'Quay lại trang chủ') : 'Quay lại trang chủ') : 'Return Home';
        }

        if (window.TempoRecoverySetup && typeof window.TempoRecoverySetup.close === 'function') {
            window.TempoRecoverySetup.close();
        }

        document.querySelectorAll('.screen-container').forEach(screen => {
            screen.classList.add('hidden');
        });
        const target = document.getElementById('screen-stress-check');
        if (target) {
            target.classList.remove('hidden');
        }
        if (window.location.hash !== '#stress-check') {
            window.location.hash = '#stress-check';
        }
        if (window.TempoApp && typeof window.TempoApp.updateNavActiveState === 'function') {
            window.TempoApp.updateNavActiveState('stress-check');
        }
        const modalAdjust = document.getElementById('modal-selfcheck-adjust');
        const isAdjustModalOpen = modalAdjust && !modalAdjust.classList.contains('hidden');
        if (!isAdjustModalOpen && window.TempoSelfCheckWorkspace && typeof window.TempoSelfCheckWorkspace.render === 'function') {
            window.TempoSelfCheckWorkspace.render();
        }
    }

    function executeStrackAction(action = 'open', options = {}) {
        const isAuthenticated = isUserAuthenticated();
        if (!isAuthenticated) {
            console.warn("[TempoMode] Protected route action blocked: Strack requires authentication.");
            openStrack(action, options);
            return;
        }

        if (action === 'setup') {
            if (activeContext === MODES.RECOVERY && window.TempoRecoverySetup && typeof window.TempoRecoverySetup.open === 'function') {
                window.TempoRecoverySetup.open(options.stage || 1);
            } else if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.openSetup === 'function') {
                window.TempoRecoverySelfCheck.openSetup();
            } else {
                showStressCheckScreen();
            }
        } else if (action === 'checkin') {
            if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.openDailyCheckin === 'function') {
                window.TempoRecoverySelfCheck.openDailyCheckin(Boolean(options.isEdit));
            } else {
                showStressCheckScreen();
            }
        } else if (action === 'manage' || action === 'adjust' || action === 'add') {
            showStressCheckScreen();
            if (window.TempoSelfCheckWorkspace && typeof window.TempoSelfCheckWorkspace.openAddTracking === 'function') {
                window.TempoSelfCheckWorkspace.openAddTracking();
            }
        } else if (action === 'history') {
            if (window.TempoSelfCheckHistory && typeof window.TempoSelfCheckHistory.open === 'function') {
                window.TempoSelfCheckHistory.open();
            } else if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.handleAction === 'function') {
                window.TempoRecoverySelfCheck.handleAction('history');
            } else {
                showStressCheckScreen();
            }
        } else if (action === 'view') {
            if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.openViewToday === 'function') {
                window.TempoRecoverySelfCheck.openViewToday();
            } else if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.openDailyCheckin === 'function') {
                window.TempoRecoverySelfCheck.openDailyCheckin(true);
            } else {
                showStressCheckScreen();
            }
        } else if (action === 'edit') {
            if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.handleAction === 'function') {
                window.TempoRecoverySelfCheck.handleAction('edit');
            } else if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.openDailyCheckin === 'function') {
                window.TempoRecoverySelfCheck.openDailyCheckin(true);
            } else {
                showStressCheckScreen();
            }
        } else {
            // General open action: opens Tempo Self-check tool page
            showStressCheckScreen();
            if (options && options.openAdjust) {
                const active = window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.getActiveTrackers === 'function'
                    ? window.TempoRecoverySelfCheck.getActiveTrackers()
                    : [];
                if (active.length === 0 && window.TempoSelfCheckWorkspace && typeof window.TempoSelfCheckWorkspace.openAddTracking === 'function') {
                    window.TempoSelfCheckWorkspace.openAddTracking();
                }
            }
        }
    }

    /**
     * Stable mapping from internal destination identifiers to UI display labels.
     */
    function getDestinationDisplayName(dest) {
        if (!dest) return '';
        const d = String(dest).toLowerCase();
        if (d === 'strack' || d === 'stress-check') return 'Self-check';
        if (d === 'ucheck' || d === 'unclear' || d === 'unclear-mode') return 'Unclear Mode assessment';
        if (d === 'plan-workspace') return 'Working Plan';
        if (d === 'emergency' || d === 'urgent' || d === 'urmode') return 'Urgent Mode';
        if (d === 'recovery' || d === 'rmode') return 'Recovery Mode';
        return dest;
    }

    /**
     * Returns to the source context dashboard from which a tool/assessment was opened.
     */
    function returnToSourceContext() {
        navigateToActiveDashboard();
    }

    /**
     * Resolves the canonical dashboard context associated with the user's active context.
     * Preserves originating mode when inside a shared assessment/tool flow like Ucheck.
     */
    function resolveActiveDashboardContext() {
        // 1. Check originating mode from shared tool session
        const origin = getOriginatingMode();
        if (origin === 'recovery' || origin === MODES.RECOVERY) return MODES.RECOVERY;
        if (origin === 'emergency' || origin === MODES.EMERGENCY) return MODES.EMERGENCY;

        if (sourceContext === 'recovery' || sourceContext === MODES.RECOVERY) return MODES.RECOVERY;
        if (sourceContext === 'emergency' || sourceContext === MODES.EMERGENCY) return MODES.EMERGENCY;

        // 2. Check activeContext in memory (primary mode)
        if (activeContext === MODES.EMERGENCY) return MODES.EMERGENCY;
        if (activeContext === MODES.RECOVERY) return MODES.RECOVERY;

        // 3. Check established context in localStorage for authenticated user
        const persisted = getUserPersistedActiveContext();
        if (persisted === MODES.EMERGENCY) return MODES.EMERGENCY;
        if (persisted === MODES.RECOVERY) return MODES.RECOVERY;

        // 4. Default Entry Home
        return MODES.DEFAULT;
    }

    /**
     * Navigates directly to the dashboard associated with the user's active context.
     * Cleans up shared tool sessions, resets nested flow views, and closes open modals.
     */
    function navigateToActiveDashboard() {
        const dest = resolveActiveDashboardContext();

        // Clear active shared tool session
        activeSharedTool = null;
        try {
            sessionStorage.removeItem('tempo_active_shared_tool');
        } catch (e) {}

        // Reset any in-flight Ucheck flow state back to clean home view
        if (window.TempoUnclearMode && typeof window.TempoUnclearMode.resetFlowState === 'function') {
            window.TempoUnclearMode.resetFlowState();
        } else {
            try {
                const uid = window.TempoAuth && typeof window.TempoAuth.getCurrentUserId === 'function' ? window.TempoAuth.getCurrentUserId() : null;
                if (uid) sessionStorage.removeItem(`tempo_unclear_in_flow_${uid}`);
            } catch (e) {}
        }

        // Close any open modals
        if (window.TempoRecoverySelfCheck) {
            if (typeof window.TempoRecoverySelfCheck.closeManage === 'function') window.TempoRecoverySelfCheck.closeManage();
            if (typeof window.TempoRecoverySelfCheck.closeDailyCheckin === 'function') window.TempoRecoverySelfCheck.closeDailyCheckin();
            if (typeof window.TempoRecoverySelfCheck.closeTrackerModal === 'function') window.TempoRecoverySelfCheck.closeTrackerModal();
            if (typeof window.TempoRecoverySelfCheck.closeViewToday === 'function') window.TempoRecoverySelfCheck.closeViewToday();
        }
        if (window.TempoRecoverySetup && typeof window.TempoRecoverySetup.close === 'function') {
            window.TempoRecoverySetup.close();
        }
        if (window.TempoCommunity && typeof window.TempoCommunity.closeCommunityModal === 'function') {
            window.TempoCommunity.closeCommunityModal();
        }
        closeChangeModeModal();
        closeAllModeDropdowns();
        closeHelpSelectionModal();

        // Clear temporary Ucheck originating mode upon returning to the dashboard
        clearOriginatingMode();

        if (dest === MODES.EMERGENCY) {
            transitionContext(MODES.EMERGENCY, { silent: true, skipSetupCheck: true });
        } else if (dest === MODES.RECOVERY) {
            transitionContext(MODES.RECOVERY, { silent: true, skipSetupCheck: true });
        } else {
            transitionContext(null, { silent: true, skipSetupCheck: true });
        }

        if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
            window.TempoApp.navigateTo('today');
        }

        try {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        } catch (e) {
            window.scrollTo(0, 0);
        }
    }

    /**
     * Legacy adapter for requestMode.
     */
    function requestMode(targetMode) {
        if (targetMode === MODES.UNCLEAR) {
            const origin = (activeContext === MODES.EMERGENCY ? 'emergency' : (activeContext === MODES.RECOVERY ? 'recovery' : (getOriginatingMode() || 'entry')));
            openUcheck({ sourceContext: origin });
            return;
        }
        if (targetMode === MODES.EMERGENCY || targetMode === 'urgent') {
            requestContext(MODES.EMERGENCY, 'selector');
            return;
        }
        if (targetMode === MODES.RECOVERY) {
            requestContext(MODES.RECOVERY, 'selector');
            return;
        }
        transitionContext(null);
    }

    /**
     * Handles canceling the auth gate modal.
     * Clears pendingIntent and returns to the original source context.
     */
    function handleAuthCancel() {
        if (pendingIntent) {
            const origin = pendingIntent.sourceContext || pendingIntent.source || sourceContext || 'entry';
            clearPendingIntent();
            activeSharedTool = null;
            try {
                const savedTool = sessionStorage.getItem('tempo_active_shared_tool');
                if (savedTool === 'ucheck') {
                    activeSharedTool = 'ucheck';
        try {
            sessionStorage.setItem('tempo_active_shared_tool', 'ucheck');
        } catch (e) {}
                }
            } catch (e) {}

            const isAuthenticated = window.TempoAuth && typeof window.TempoAuth.getCurrentUser === 'function' && !!window.TempoAuth.getCurrentUser();
            if (!isAuthenticated) {
                activeContext = null;
                sourceContext = 'entry';
                renderActiveModeHome();
                if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
                    window.TempoApp.navigateTo('today');
                }
                return;
            }

            let target = origin;
            if (target !== 'emergency' && target !== 'recovery' && target !== 'unclear') {
                const persisted = getUserPersistedActiveContext();
                if (persisted === MODES.EMERGENCY || persisted === MODES.RECOVERY || persisted === MODES.UNCLEAR) {
                    target = persisted;
                }
            }

            if (target === 'emergency' || target === MODES.EMERGENCY) {
                activeContext = MODES.EMERGENCY;
                sourceContext = 'emergency';
                renderActiveModeHome();
            } else if (target === 'recovery' || target === MODES.RECOVERY) {
                activeContext = MODES.RECOVERY;
                sourceContext = 'recovery';
                renderActiveModeHome();
            } else if (target === 'unclear' || target === MODES.UNCLEAR) {
                activeContext = MODES.UNCLEAR;
                sourceContext = 'unclear';
                renderActiveModeHome();
            } else {
                activeContext = null;
                sourceContext = 'entry';
                renderActiveModeHome();
            }
            if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
                window.TempoApp.navigateTo('today');
            }
        }
    }

    /**
     * Called immediately after successful sign in or sign up.
     * Fulfills pendingIntent without incorrectly forcing emergency mode on Wplan tools.
     */
    function handleAuthSuccess() {
        const isAuth = Boolean(
            window.TempoAuth && 
            typeof window.TempoAuth.getCurrentUser === 'function' && 
            window.TempoAuth.getCurrentUser() &&
            (typeof window.TempoAuth.getAuthState !== 'function' || window.TempoAuth.getAuthState() === 'authenticated') &&
            !(typeof window.TempoAuth.isRegistrationInProgress === 'function' && window.TempoAuth.isRegistrationInProgress())
        );

        if (!isAuth) {
            console.warn("[TempoMode] handleAuthSuccess rejected: user is not authenticated.");
            return false;
        }

        let intent = pendingIntent;
        if (!intent) {
            try {
                const raw = localStorage.getItem('tempo_pending_intent');
                if (raw) intent = JSON.parse(raw);
            } catch (e) {}
        }
        if (!intent) {
            const legacyPending = localStorage.getItem('tempo_pending_mode');
            if (legacyPending && Object.values(MODES).includes(legacyPending)) {
                intent = { type: 'mode', destination: legacyPending, action: 'select', source: 'entry' };
            }
        }

        // Invariant 18D: Validate pending intent before resume
        if (intent && !isValidPendingIntent(intent)) {
            console.warn("[TempoMode] Invalid pending intent rejected:", intent);
            clearPendingIntent();
            intent = null;
        }

        // Parallel restoration: resolve user's established context in background/state
        // Invariant 18F: Account isolation (only this uid's established context)
        const uid = window.TempoAuth && typeof window.TempoAuth.getCurrentUserId === 'function' ? window.TempoAuth.getCurrentUserId() : null;
        let established = getUserPersistedActiveContext(uid);

        const currentActive = activeContext;
        const intentSource = intent ? (intent.source || intent.sourceContext) : null;
        const dest = intent ? (intent.destination || intent.tool || '').toLowerCase() : '';
        const isToolOrAssessment = intent && (
            dest === 'strack' || dest === 'stress-check' ||
            intent.type === 'ucheck' || dest === 'ucheck' || dest === 'unclear' || dest === 'unclear-mode' ||
            dest === 'plan-workspace' || intent.type === 'tool'
        );

        let resolvedContext = null;
        if (established === MODES.EMERGENCY || established === MODES.RECOVERY || established === MODES.UNCLEAR) {
            resolvedContext = established;
        } else if (established === MODES.DEFAULT) {
            resolvedContext = null;
        } else if (intentSource === 'emergency' || currentActive === MODES.EMERGENCY) {
            resolvedContext = MODES.EMERGENCY;
        } else if (intentSource === 'recovery' || currentActive === MODES.RECOVERY) {
            resolvedContext = MODES.RECOVERY;
        }

        if (resolvedContext === MODES.EMERGENCY) {
            activeContext = MODES.EMERGENCY;
            sourceContext = 'emergency';
            try {
                localStorage.setItem('tempo_current_mode', MODES.EMERGENCY);
                localStorage.setItem('tempo_established_context', MODES.EMERGENCY);
                if (uid) localStorage.setItem('tempo_user_established_context_' + uid, MODES.EMERGENCY);
            } catch (e) {}
        } else if (resolvedContext === MODES.RECOVERY) {
            activeContext = MODES.RECOVERY;
            sourceContext = 'recovery';
            try {
                localStorage.setItem('tempo_current_mode', MODES.RECOVERY);
                localStorage.setItem('tempo_established_context', MODES.RECOVERY);
                if (uid) localStorage.setItem('tempo_user_established_context_' + uid, MODES.RECOVERY);
            } catch (e) {}
        } else if (resolvedContext === MODES.UNCLEAR) {
            activeContext = MODES.UNCLEAR;
            sourceContext = 'unclear';
            try {
                localStorage.setItem('tempo_current_mode', MODES.UNCLEAR);
                localStorage.setItem('tempo_established_context', MODES.UNCLEAR);
                if (uid) localStorage.setItem('tempo_user_established_context_' + uid, MODES.UNCLEAR);
            } catch (e) {}
        } else {
            activeContext = null;
            sourceContext = 'entry';
            try {
                localStorage.setItem('tempo_current_mode', MODES.DEFAULT);
                localStorage.removeItem('tempo_established_context');
            } catch (e) {}
        }

        if (intent) {
            clearPendingIntent();
            const isMode = intent.type === 'mode' || dest === 'emergency' || dest === 'recovery' || dest === 'urgent' || dest === 'urmode' || dest === 'rmode';
            const isUcheck = intent.type === 'ucheck' || dest === 'ucheck' || dest === 'unclear' || dest === 'unclear-mode';
            const isStrack = dest === 'strack' || dest === 'stress-check';

            if (isMode) {
                const target = (dest === 'urgent' || dest === 'urmode' || dest === 'emergency') ? MODES.EMERGENCY : MODES.RECOVERY;
                transitionContext(target, { silent: true });

                if (target === MODES.EMERGENCY) {
                    if (window.TempoApp) {
                        const hasPlan = window.TempoPlanStore && typeof window.TempoPlanStore.hasActivePlan === 'function' && window.TempoPlanStore.hasActivePlan('emergency');
                        if (hasPlan) {
                            window.TempoApp.navigateTo('today');
                        } else {
                            window.TempoApp.navigateTo('emergency');
                        }
                        window.TempoApp.showToast("Welcome! Resuming your Urgent Mode setup.");
                    }
                } else if (target === MODES.RECOVERY) {
                    if (window.TempoApp) {
                        window.TempoApp.navigateTo('today');
                        window.TempoApp.showToast("Welcome! Entering Recovery Mode.");
                    }
                }
                return true;
            } else if (isUcheck) {
                // Resume Ucheck without changing activeContext
                const savedSource = (resolvedContext === MODES.EMERGENCY ? 'emergency' : (resolvedContext === MODES.RECOVERY ? 'recovery' : (resolvedContext === MODES.UNCLEAR ? 'unclear' : (intent.source || intent.sourceContext || 'entry'))));
                sourceContext = savedSource;
                setOriginatingMode(savedSource);
                openUcheck(Object.assign({}, intent.requiredParams || intent.options || {}, { sourceContext: savedSource }));
                if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                    window.TempoApp.showToast("Signed in. Resuming Unclear Mode assessment.");
                }
                return true;
            } else if (isStrack) {
                // Resume Strack (Self-check) preserving user's established activeContext
                const savedSource = (resolvedContext === MODES.RECOVERY ? 'recovery' : (resolvedContext === MODES.EMERGENCY ? 'emergency' : (resolvedContext === MODES.UNCLEAR ? 'unclear' : (intent.source || intent.sourceContext || 'entry'))));
                sourceContext = savedSource;
                setOriginatingMode(savedSource);
                const strackParams = Object.assign({}, intent.requiredParams || intent.options || {}, { sourceContext: savedSource });
                openStrack(intent.action || 'open', strackParams);
                if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                    window.TempoApp.showToast("Signed in. Resuming Self-check.");
                }
                return true;
            } else {
                // Resume tool without forcing emergency mode
                const targetDest = intent.destination || intent.tool;
                if (targetDest && window.TempoApp) {
                    const sub = intent.requiredParams && (intent.requiredParams.tab || intent.requiredParams.section);
                    window.TempoApp.navigateTo(targetDest, sub);
                    const toolName = targetDest === 'plan-workspace' ? 'Working Plan' : (targetDest === 'personal-space' ? 'Personal Space' : (targetDest === 'posts' ? (sub === 'messages' ? 'Direct Messages' : 'Community Posts') : (targetDest === 'stress-check' ? 'Self-check' : 'tool')));
                    window.TempoApp.showToast(`Signed in. Resuming ${toolName}.`);
                }
                return true;
            }
        }

        renderShellIndicator();
        renderActiveModeHome();
        return false;
    }

    /**
     * Handles user logout.
     * Transitions in-memory session to Entry Home (activeContext = null) for the guest session.
     * Clears session-scoped pendingIntent, activeSharedTool, and resets view to Entry Home.
     * Preserves the signed-out user's established active context in localStorage
     * so it can be resumed upon their next login.
     */
    function handleSignOut() {
        activeContext = null;
        activeSharedTool = null;
        sourceContext = 'entry';
        clearPendingIntent();

        try {
            localStorage.setItem('tempo_current_mode', MODES.DEFAULT);
            localStorage.removeItem('tempo_established_context');
        } catch (e) {}

        renderShellIndicator();
        closeChangeModeModal();
        closeAllModeDropdowns();
        if (window.TempoRecoverySetup && typeof window.TempoRecoverySetup.close === 'function') {
            window.TempoRecoverySetup.close();
        }
        if (window.TempoRecoverySelfCheck) {
            if (typeof window.TempoRecoverySelfCheck.closeManage === 'function') window.TempoRecoverySelfCheck.closeManage();
            if (typeof window.TempoRecoverySelfCheck.closeDailyCheckin === 'function') window.TempoRecoverySelfCheck.closeDailyCheckin();
            if (typeof window.TempoRecoverySelfCheck.closeTrackerModal === 'function') window.TempoRecoverySelfCheck.closeTrackerModal();
            if (typeof window.TempoRecoverySelfCheck.closeViewToday === 'function') window.TempoRecoverySelfCheck.closeViewToday();
        }
        renderActiveModeHome();
    }

    /**
     * Sets the centralized mode state (legacy adapter).
     */
    function setMode(newMode, options = {}) {
        if (newMode === 'urgent') {
            newMode = MODES.EMERGENCY;
        }
        if (newMode === MODES.UNCLEAR) {
            const origin = options.sourceContext || (activeContext === MODES.EMERGENCY ? 'emergency' : (activeContext === MODES.RECOVERY ? 'recovery' : (getOriginatingMode() || 'entry')));
            openUcheck(Object.assign({}, options, { sourceContext: origin }));
            return;
        }
        if (newMode === MODES.EMERGENCY) {
            transitionContext(MODES.EMERGENCY, options);
            return;
        }
        if (newMode === MODES.RECOVERY) {
            transitionContext(MODES.RECOVERY, options);
            return;
        }
        transitionContext(null, options);
    }

    // =========================================================================
    // GLOBAL SHELL INDICATOR & MODE SELECTOR DROPDOWNS
    // =========================================================================

    function renderShellIndicator() {
        const curMode = getMode();
        updateNavbarForMode(curMode);

        const shell = document.getElementById('mode-indicator-shell');
        if (!shell) return;

        // Explicit rendering condition:
        // In Recovery Mode, Urmode, Entry Home, and Unclear Mode,
        // the navbar mode dropdown/pill is hidden.
        // Mode switching is handled via in-dashboard card selectors (#btn-home-mode-selector).
        shell.classList.add('hidden');
        shell.classList.remove('flex');

        const dropdown = document.getElementById('navbar-mode-dropdown');
        if (dropdown) dropdown.classList.add('hidden');
        const trigger = document.getElementById('btn-mode-indicator-trigger');
        if (trigger) trigger.setAttribute('aria-expanded', 'false');
    }

    function renderModeDropdownHTML(origin = 'home') {
        const curMode = getMode();
        const showUrgent = curMode !== MODES.EMERGENCY;
        const showRecovery = curMode !== MODES.RECOVERY;
        const showUnclear = curMode !== MODES.UNCLEAR;

        let itemsHTML = '';

        if (showUrgent) {
            itemsHTML += `
                <!-- Urgent Mode -->
                <button type="button" onclick="window.TempoMode.selectModeFromDropdown('${MODES.EMERGENCY}', '${origin}')"
                        class="w-full text-left p-2.5 rounded-xl hover:bg-[#FFF4EC] flex items-start justify-between group transition cursor-pointer" role="menuitem">
                    <div class="flex items-start space-x-2.5">
                        <span class="text-base text-[#FF6B2C] mt-0.5 leading-none">⚡</span>
                        <div>
                            <div class="text-xs font-bold text-[#202124] group-hover:text-[#FF6B2C] transition-colors">${window.t ? window.t('modes.urgent.name', {}, 'Urgent Mode') : 'Urgent Mode'}</div>
                            <div class="text-[11px] text-[#6F6B68]">${window.t ? window.t('modes.urgent.tagline', {}, "Handle what's urgent") : "Handle what's urgent"}</div>
                        </div>
                    </div>
                </button>
            `;
        }

        if (showRecovery) {
            itemsHTML += `
                <!-- Recovery Mode -->
                <button type="button" onclick="window.TempoMode.selectModeFromDropdown('${MODES.RECOVERY}', '${origin}')"
                        class="w-full text-left p-2.5 rounded-xl hover:bg-[#EDF7F1] flex items-start justify-between group transition cursor-pointer" role="menuitem">
                    <div class="flex items-start space-x-2.5">
                        <span class="text-base text-[#166545] mt-0.5 leading-none">🌱</span>
                        <div>
                            <div class="text-xs font-bold text-[#202124] group-hover:text-[#166545] transition-colors">${window.t ? window.t('modes.recovery.name', {}, 'Recovery Mode') : 'Recovery Mode'}</div>
                            <div class="text-[11px] text-[#6F6B68]">${window.t ? window.t('modes.recovery.tagline', {}, 'Slow down and recover') : 'Slow down and recover'}</div>
                        </div>
                    </div>
                </button>
            `;
        }

        if (showUnclear) {
            itemsHTML += `
                <!-- Unclear Mode -->
                <button type="button" onclick="window.TempoMode.selectModeFromDropdown('${MODES.UNCLEAR}', '${origin}')"
                        class="w-full text-left p-2.5 rounded-xl hover:bg-[#FEF7EC] flex items-start justify-between group transition cursor-pointer" role="menuitem">
                    <div class="flex items-start space-x-2.5">
                        <span class="text-base text-[#9A5B13] mt-0.5 leading-none">🧭</span>
                        <div>
                            <div class="text-xs font-bold text-[#202124] group-hover:text-[#9A5B13] transition-colors">${window.t ? window.t('modes.unclear.name', {}, 'Unclear Mode') : 'Unclear Mode'}</div>
                            <div class="text-[11px] text-[#6F6B68]">${window.t ? window.t('modes.unclear.tagline', {}, "Figure out what's going on") : "Figure out what's going on"}</div>
                        </div>
                    </div>
                </button>
            `;
        }

        return `
            <div class="py-1 space-y-1" role="menu" aria-orientation="vertical">
                ${itemsHTML}
            </div>
        `;
    }

    /**
     * Synchronizes mode selector DOM elements across containers so the active
     * container always holds the canonical IDs (#btn-home-mode-selector, #home-mode-selector-dropdown)
     * and inactive containers do not hold conflicting/stale IDs.
     */
    function syncModeSelectorDOM(activeMode) {
        const mode = activeMode || getMode();
        const containers = [
            { box: document.getElementById('emode-home-content'), mode: MODES.EMERGENCY },
            { box: document.getElementById('rmode-home-content'), mode: MODES.RECOVERY },
            { box: document.getElementById('umode-home-content'), mode: MODES.UNCLEAR }
        ];

        containers.forEach(({ box, mode: boxMode }) => {
            if (!box) return;
            const isActive = boxMode === mode;
            const dropdown = box.querySelector('[id^="home-mode-selector-dropdown"]');
            if (dropdown) {
                dropdown.id = isActive ? 'home-mode-selector-dropdown' : 'home-mode-selector-dropdown-inactive';
                if (!isActive) dropdown.classList.add('hidden');
            }
            const btn = box.querySelector('[id^="btn-home-mode-selector"]');
            if (btn) {
                btn.id = isActive ? 'btn-home-mode-selector' : 'btn-home-mode-selector-inactive';
                if (!isActive) btn.setAttribute('aria-expanded', 'false');
            }
            const wrapper = box.querySelector('[id^="home-mode-selector-wrapper"]');
            if (wrapper) {
                wrapper.id = isActive ? 'home-mode-selector-wrapper' : 'home-mode-selector-wrapper-inactive';
            }
        });
    }

    function resolveHomeDropdownElements(event) {
        const curMode = getMode();
        syncModeSelectorDOM(curMode);

        let trigger = null;
        if (event && event.currentTarget) {
            trigger = event.currentTarget;
        } else if (event && event.target) {
            trigger = event.target.closest('#btn-home-mode-selector, [data-tempo-ui="mode-selector-btn"], [id^="btn-home-mode-selector"]');
        }
        if (!trigger) {
            const activeBox = document.querySelector('#screen-today > div:not(.hidden)');
            if (activeBox) {
                trigger = activeBox.querySelector('#btn-home-mode-selector, [data-tempo-ui="mode-selector-btn"]');
            }
        }
        if (!trigger) {
            trigger = document.getElementById('btn-home-mode-selector');
        }

        let dropdown = null;
        if (trigger) {
            const wrapper = trigger.closest('#home-mode-selector-wrapper, [id^="home-mode-selector-wrapper"]') || trigger.parentElement;
            if (wrapper) {
                dropdown = wrapper.querySelector('#home-mode-selector-dropdown, [id^="home-mode-selector-dropdown"]');
            }
        }
        if (!dropdown) {
            const activeBox = document.querySelector('#screen-today > div:not(.hidden)');
            if (activeBox) {
                dropdown = activeBox.querySelector('#home-mode-selector-dropdown, [id^="home-mode-selector-dropdown"]');
            }
        }
        if (!dropdown) {
            dropdown = document.getElementById('home-mode-selector-dropdown');
        }

        return { trigger, dropdown };
    }

    function toggleModeDropdown(event) {
        if (event) {
            event.stopPropagation();
            event.preventDefault();
        }
        const { trigger, dropdown } = resolveHomeDropdownElements(event);
        if (!dropdown) return;
        const isHidden = dropdown.classList.contains('hidden');
        closeAllModeDropdowns();
        if (isHidden) {
            dropdown.innerHTML = renderModeDropdownHTML('home');
            dropdown.classList.remove('hidden');
            if (trigger) trigger.setAttribute('aria-expanded', 'true');
        }
    }

    function toggleNavbarModeDropdown(event) {
        if (event) {
            event.stopPropagation();
            event.preventDefault();
        }
        const dropdown = document.getElementById('navbar-mode-dropdown');
        if (!dropdown) return;
        const isHidden = dropdown.classList.contains('hidden');
        closeAllModeDropdowns();
        if (isHidden) {
            dropdown.innerHTML = renderModeDropdownHTML('navbar');
            dropdown.classList.remove('hidden');
            const trigger = document.getElementById('btn-mode-indicator-trigger');
            if (trigger) trigger.setAttribute('aria-expanded', 'true');
        }
    }

    function closeAllModeDropdowns() {
        document.querySelectorAll('#home-mode-selector-dropdown, [id^="home-mode-selector-dropdown"]').forEach(d => {
            d.classList.add('hidden');
        });
        document.querySelectorAll('#btn-home-mode-selector, [data-tempo-ui="mode-selector-btn"], [id^="btn-home-mode-selector"]').forEach(t => {
            t.setAttribute('aria-expanded', 'false');
        });
        document.querySelectorAll('#navbar-mode-dropdown').forEach(d => {
            d.classList.add('hidden');
        });
        document.querySelectorAll('#btn-mode-indicator-trigger').forEach(t => {
            t.setAttribute('aria-expanded', 'false');
        });
    }

    function selectModeFromDropdown(targetMode, origin = 'home') {
        closeAllModeDropdowns();
        if (targetMode === getMode()) return;
        if (targetMode === MODES.UNCLEAR) {
            const curMode = activeContext === MODES.EMERGENCY ? 'emergency' : (activeContext === MODES.RECOVERY ? 'recovery' : 'entry');
            setOriginatingMode(curMode);
        }
        if (targetMode === MODES.EMERGENCY || targetMode === 'emergency' || targetMode === 'urgent') {
            if (window.TempoUrmodeFlow && typeof window.TempoUrmodeFlow.queueResetPopup === 'function') {
                window.TempoUrmodeFlow.queueResetPopup();
            }
        }
        requestMode(targetMode);
    }

    function openChangeModeModal() {
        const modal = document.getElementById('modal-change-mode');
        if (!modal) return;

        const optEmergency = document.getElementById('change-mode-opt-emergency');
        const optRecovery = document.getElementById('change-mode-opt-recovery');
        const optUnclear = document.getElementById('change-mode-opt-unclear');
        const footerBtn = document.getElementById('change-mode-footer-btn');

        const curMode = getMode();
        if (optEmergency) optEmergency.classList.toggle('hidden', curMode === MODES.EMERGENCY);
        if (optRecovery) optRecovery.classList.toggle('hidden', curMode === MODES.RECOVERY);
        if (optUnclear) optUnclear.classList.toggle('hidden', curMode === MODES.UNCLEAR);

        if (footerBtn) {
            footerBtn.textContent = `Stay in ${getModeDisplayName(curMode)}`;
        }

        modal.classList.remove('hidden');
        document.body.classList.add('overflow-hidden');
    }

    function closeChangeModeModal() {
        const modal = document.getElementById('modal-change-mode');
        if (modal) {
            modal.classList.add('hidden');
            document.body.classList.remove('overflow-hidden');
        }
    }

    function openHelpSelectionModal() {
        if (window.TempoApp && typeof window.TempoApp.openRoutingModal === 'function') {
            window.TempoApp.openRoutingModal();
        } else {
            const modal = document.getElementById('modal-routing-selection');
            if (modal) {
                modal.classList.remove('hidden');
                document.body.classList.add('overflow-hidden');
                const firstCard = modal.querySelector('.state-choice-card');
                if (firstCard) firstCard.focus();
            }
        }
    }

    function closeHelpSelectionModal() {
        const modal = document.getElementById('modal-routing-selection');
        if (modal) {
            modal.classList.add('hidden');
            document.body.classList.remove('overflow-hidden');
        }
    }

    function selectModeOption(targetMode) {
        closeChangeModeModal();
        if (targetMode === getMode()) return;
        if (targetMode === MODES.UNCLEAR) {
            const curMode = activeContext === MODES.EMERGENCY ? 'emergency' : (activeContext === MODES.RECOVERY ? 'recovery' : 'entry');
            setOriginatingMode(curMode);
        }
        if (targetMode === MODES.EMERGENCY || targetMode === 'emergency' || targetMode === 'urgent') {
            if (window.TempoUrmodeFlow && typeof window.TempoUrmodeFlow.queueResetPopup === 'function') {
                window.TempoUrmodeFlow.queueResetPopup();
            }
        }
        requestMode(targetMode);
    }

    function updateAuthGateBanners(targetMode) {
        document.querySelectorAll('.auth-mode-gate-banner').forEach(banner => {
            const titleEl = banner.querySelector('.auth-mode-gate-title');
            const descEl = banner.querySelector('.auth-mode-gate-desc');

            if (targetMode && targetMode !== MODES.DEFAULT) {
                banner.classList.remove('hidden');
                if (targetMode === MODES.UNCLEAR || targetMode === 'ucheck') {
                    if (titleEl) titleEl.textContent = 'Unclear Mode requires an account';
                    if (descEl) descEl.textContent = 'Sign in or register below to save your assessment. You will resume Unclear Mode immediately after.';
                } else {
                    if (titleEl) titleEl.textContent = `${getModeDisplayName(targetMode)} requires an account`;
                    if (descEl) descEl.textContent = `Sign in or register below to save your plan. You will enter ${getModeDisplayName(targetMode)} immediately after.`;
                }
            } else {
                banner.classList.add('hidden');
            }
        });
    }

    /**
     * Updates the main navigation bar according to the active mode/context:
     * - Entry Home: About · Check · Plan · Community
     * - Urmode:     About · Check · Assessment · Community
     * - Rmode:      About · Plan · Assessment · Community
     */
    function updateNavbarForMode(activeMode) {
        let mode = activeMode !== undefined ? activeMode : getMode();
        if (isUCheckActiveView()) {
            mode = MODES.UNCLEAR;
        }

        const checkLink = document.getElementById('nav-link-check');
        const planLink = document.getElementById('nav-link-plan');
        const isVi = isViLocale();

        // Link 2: Check (Entry Home, Urmode & UCheck) vs Plan (Recovery Mode)
        if (checkLink) {
            if (mode === MODES.RECOVERY) {
                const label = window.t ? window.t('nav.plan', {}, 'Plan') : 'Plan';
                checkLink.textContent = label;
                checkLink.setAttribute('href', '#recovery-working-plan');
                checkLink.setAttribute('title', label);
                checkLink.onclick = function(e) {
                    if (e && e.preventDefault) e.preventDefault();
                    if (window.TempoApp && typeof window.TempoApp.scrollToRecoveryPlan === 'function') {
                        window.TempoApp.scrollToRecoveryPlan();
                    } else if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
                        window.TempoApp.navigateTo('plan');
                    }
                    return false;
                };
            } else if (mode === MODES.UNCLEAR) {
                // UCheck Navbar: "Check" in both VI and EN
                const label = window.t ? window.t('nav.check', {}, 'Check') : 'Check';
                checkLink.textContent = label;
                checkLink.setAttribute('href', '#stress-check');
                checkLink.setAttribute('title', label);
                checkLink.onclick = function(e) {
                    if (e && e.preventDefault) e.preventDefault();
                    if (window.TempoMode && typeof window.TempoMode.openStrack === 'function') {
                        window.TempoMode.openStrack('open', { sourceContext: sourceContext || 'entry' });
                    } else if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
                        window.TempoApp.navigateTo('stress-check');
                    }
                    return false;
                };
            } else if (mode === MODES.DEFAULT || !mode || mode === 'default') {
                const label = window.t ? window.t('nav.check', {}, 'Check') : 'Check';
                checkLink.textContent = label;
                checkLink.setAttribute('href', '#stress-check');
                checkLink.setAttribute('title', label);
                checkLink.onclick = function(e) {
                    if (e && e.preventDefault) e.preventDefault();
                    if (window.TempoMode && typeof window.TempoMode.openStrack === 'function') {
                        window.TempoMode.openStrack('open', { sourceContext: 'entry' });
                    } else if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
                        window.TempoApp.navigateTo('stress-check');
                    }
                    return false;
                };
            } else {
                const label = window.t ? window.t('nav.check', {}, 'Check') : 'Check';
                checkLink.textContent = label;
                checkLink.setAttribute('href', '#stress-check');
                checkLink.setAttribute('title', label);
                checkLink.onclick = function(e) {
                    if (e && e.preventDefault) e.preventDefault();
                    if (window.TempoMode && typeof window.TempoMode.openStrack === 'function') {
                        window.TempoMode.openStrack('open', { sourceContext: mode === MODES.EMERGENCY ? 'emergency' : (mode === MODES.RECOVERY ? 'recovery' : (sourceContext || 'entry')) });
                    } else if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
                        window.TempoApp.navigateTo('stress-check');
                    }
                    return false;
                };
            }
        }

        // Link 3: Plan (Entry Home) vs Assessment (Urmode & Recovery Mode) vs Test (UCheck vi)
        if (planLink) {
            if (mode === MODES.UNCLEAR) {
                // UCheck Navbar: "Test" in VI, "Assessment" in EN
                const label = isVi ? (window.t ? window.t('nav.test', {}, 'Test') : 'Test') : (window.t ? window.t('nav.assessment', {}, 'Assessment') : 'Assessment');
                planLink.textContent = label;
                planLink.setAttribute('href', '#ucheck');
                planLink.setAttribute('title', label);
                planLink.onclick = function(e) {
                    if (e && e.preventDefault) e.preventDefault();
                    if (window.TempoMode && typeof window.TempoMode.openUcheck === 'function') {
                        window.TempoMode.openUcheck({ sourceContext: sourceContext || (activeContext === MODES.RECOVERY ? 'recovery' : 'emergency') });
                    } else if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
                        window.TempoApp.navigateTo('ucheck');
                    } else {
                        window.location.hash = '#ucheck';
                    }
                    return false;
                };
            } else if (mode === MODES.DEFAULT || !mode || mode === 'default') {
                const label = 'Plan';
                planLink.textContent = label;
                planLink.setAttribute('href', '#plan-workspace');
                planLink.setAttribute('title', label);
                planLink.onclick = function(e) {
                    if (e && e.preventDefault) e.preventDefault();
                    if (window.TempoMode && typeof window.TempoMode.openPlanWorkspace === 'function') {
                        window.TempoMode.openPlanWorkspace();
                    } else if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
                        window.TempoApp.navigateTo('plan-workspace');
                    }
                    return false;
                };
            } else if (mode === MODES.EMERGENCY) {
                const label = isVi ? (window.t ? window.t('nav.test', {}, 'Test') : 'Test') : (window.t ? window.t('nav.assessment', {}, 'Assessment') : 'Assessment');
                planLink.textContent = label;
                planLink.setAttribute('href', '#ucheck');
                planLink.setAttribute('title', label);
                planLink.onclick = function(e) {
                    if (e && e.preventDefault) e.preventDefault();
                    if (window.TempoMode && typeof window.TempoMode.openUcheck === 'function') {
                        window.TempoMode.openUcheck({ sourceContext: 'emergency' });
                    } else if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
                        window.TempoApp.navigateTo('ucheck');
                    } else {
                        window.location.hash = '#ucheck';
                    }
                    return false;
                };
            } else if (mode === MODES.RECOVERY) {
                const label = isVi ? (window.t ? window.t('nav.test', {}, 'Test') : 'Test') : (window.t ? window.t('nav.assessment', {}, 'Assessment') : 'Assessment');
                planLink.textContent = label;
                planLink.setAttribute('href', '#ucheck');
                planLink.setAttribute('title', label);
                planLink.onclick = function(e) {
                    if (e && e.preventDefault) e.preventDefault();
                    if (window.TempoMode && typeof window.TempoMode.openUcheck === 'function') {
                        window.TempoMode.openUcheck({ sourceContext: 'recovery' });
                    } else if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
                        window.TempoApp.navigateTo('ucheck');
                    } else {
                        window.location.hash = '#ucheck';
                    }
                    return false;
                };
            } else {
                const label = isVi ? (window.t ? window.t('nav.tools', {}, 'Công cụ') : 'Công cụ') : (window.t ? window.t('nav.tools', {}, 'Tools') : 'Tools');
                planLink.textContent = label;
                planLink.setAttribute('href', '#enjoy-tempo-tools');
                planLink.setAttribute('title', label);
                planLink.onclick = function(e) {
                    if (e && e.preventDefault) e.preventDefault();
                    if (window.TempoApp && typeof window.TempoApp.scrollToEnjoyTempoTools === 'function') {
                        window.TempoApp.scrollToEnjoyTempoTools();
                    }
                    return false;
                };
            }
        }

        // Shared navigation rendering condition:
        // Hide the navbar mode dropdown/pill across all modes (Recovery, Urgent, Entry, Unclear)
        const shell = document.getElementById('mode-indicator-shell');
        if (shell) {
            shell.classList.add('hidden');
            shell.classList.remove('flex');
        }
        const dropdown = document.getElementById('navbar-mode-dropdown');
        if (dropdown) dropdown.classList.add('hidden');
        const trigger = document.getElementById('btn-mode-indicator-trigger');
        if (trigger) trigger.setAttribute('aria-expanded', 'false');
    }

    // =========================================================================
    // CENTRALIZED MODE DASHBOARD VISIBILITY CONTROLLER
    // Strict mutual exclusivity: exactly one mode dashboard is visible on Home.
    // =========================================================================

    function applyModeVisibility(targetMode) {
        const mode = targetMode || getMode();
        const dmodeBox = document.getElementById('dmode-home-content');
        const emodeBox = document.getElementById('emode-home-content');
        const rmodeBox = document.getElementById('rmode-home-content');
        const umodeBox = document.getElementById('umode-home-content');

        if (dmodeBox) dmodeBox.classList.toggle('hidden', mode !== MODES.DEFAULT);
        if (emodeBox) emodeBox.classList.toggle('hidden', mode !== MODES.EMERGENCY);
        if (rmodeBox) rmodeBox.classList.toggle('hidden', mode !== MODES.RECOVERY);
        if (umodeBox) umodeBox.classList.toggle('hidden', mode !== MODES.UNCLEAR);

        const mainEl = document.querySelector('main');
        if (mode === MODES.EMERGENCY) {
            document.body.style.backgroundColor = '#e6ede7';
            if (mainEl) mainEl.style.backgroundColor = '#e6ede7';
        } else if (mode === MODES.RECOVERY) {
            document.body.style.backgroundColor = '#E8ECF1';
            if (mainEl) mainEl.style.backgroundColor = '#E8ECF1';
        } else if (mode === MODES.UNCLEAR) {
            document.body.style.backgroundColor = '#FEEAE0';
            if (mainEl) mainEl.style.backgroundColor = '#FEEAE0';
        } else {
            document.body.style.backgroundColor = '#FAF7F2';
            if (mainEl) mainEl.style.backgroundColor = '#FAF7F2';
        }

        syncModeSelectorDOM(mode);
        updateNavbarForMode(mode);
    }

    // =========================================================================
    // DEFAULT HOME — CONTINUITY REDESIGN
    // Hierarchy:
    // 1. Compact greeting + date
    // 2. Your Day (shared tasks in saved order, completion toggle, subtasks, [View my plan →])
    // 3. Focus Zone + Quick Relief (paired 2-col on desktop, stacked on mobile)
    // 4. Self-check (compact card: State A, B, or C)
    // 5. Contextual card (rendered ONLY if genuine Weekly Review is ready)
    // 6. Tempo Posts (social format only, preview 1-2 posts)
    // =========================================================================

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

    function formatDurationMinutes(mins) {
        if (!mins || mins <= 0) return '';
        const h = Math.floor(mins / 60);
        const m = mins % 60;
        if (h > 0 && m > 0) return `~${h}h ${m}m`;
        if (h > 0) return `~${h}h`;
        return `~${m} min`;
    }

    function getSharedPlanContext() {
        let plan = null;
        if (window.TempoPlanWorkspace && typeof window.TempoPlanWorkspace.getActivePlan === 'function') {
            plan = window.TempoPlanWorkspace.getActivePlan();
        }
        if (!plan && window.TempoPlanStore && typeof window.TempoPlanStore.getActivePlan === 'function') {
            plan = window.TempoPlanStore.getActivePlan('emergency');
        }
        if (!plan && window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.getConfirmedPlan === 'function') {
            plan = window.TempoEmergencyFlow.getConfirmedPlan();
        }
        return plan;
    }

    function getSharedPlanTodayTasks() {
        const plan = getSharedPlanContext();
        if (!plan || !Array.isArray(plan.plannedTasks) || plan.plannedTasks.length === 0) {
            return {
                state: 'BRAND_NEW',
                todayItems: [],
                tomorrowTasksCount: 0,
                hasActivePlan: false
            };
        }

        const todayStr = getTodayISOString();
        const tomorrowObj = new Date();
        tomorrowObj.setDate(tomorrowObj.getDate() + 1);
        const tomorrowStr = getLocalTomorrowISO();

        const allPlanned = plan.plannedTasks.filter(pt => pt && pt.task);
        if (allPlanned.length === 0) {
            return {
                state: 'BRAND_NEW',
                todayItems: [],
                tomorrowTasksCount: 0,
                hasActivePlan: true
            };
        }

        const hasAnyDates = allPlanned.some(pt => pt.dayDate || pt.dayLabel);
        let todayItems = [];
        let tomorrowItems = [];

        if (!hasAnyDates) {
            todayItems = allPlanned;
        } else {
            todayItems = allPlanned.filter(pt => {
                if (pt.dayDate === todayStr) return true;
                if (pt.dayLabel) {
                    const dl = String(pt.dayLabel).toUpperCase();
                    if (dl === 'TODAY' || dl.startsWith('DAY 1')) return true;
                }
                return false;
            });
            tomorrowItems = allPlanned.filter(pt => {
                if (pt.dayDate === tomorrowStr) return true;
                if (pt.dayLabel) {
                    const dl = String(pt.dayLabel).toUpperCase();
                    if (dl === 'TOMORROW' || dl.startsWith('DAY 2')) return true;
                }
                return false;
            });
        }

        if (todayItems.length === 0) {
            return {
                state: 'NO_WORK_TODAY',
                todayItems: [],
                tomorrowTasksCount: tomorrowItems.length,
                hasActivePlan: true
            };
        }

        const allDone = todayItems.every(pt => pt.task && pt.task.completed === true);
        if (allDone) {
            return {
                state: 'TODAY_COMPLETE',
                todayItems: todayItems,
                tomorrowTasksCount: tomorrowItems.length,
                hasActivePlan: true
            };
        }

        return {
            state: 'ACTIVE_TODAY',
            todayItems: todayItems,
            tomorrowTasksCount: tomorrowItems.length,
            hasActivePlan: true
        };
    }

    function renderDmodeHeader(greetingInfo) {
        const todayObj = new Date();
        const formattedDate = window.TempoI18n ? window.TempoI18n.formatDate(todayObj, {
            weekday: 'long',
            month: 'short',
            day: 'numeric'
        }) : todayObj.toLocaleDateString('en-US', {
            weekday: 'long',
            month: 'short',
            day: 'numeric'
        });

        return `
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-[#F0ECE9]">
                <h2 class="font-heading text-2xl sm:text-3xl font-extrabold text-[#202124] tracking-tight">
                    ${escapeHTML(greetingInfo.greetingText)}
                </h2>
                <div class="text-xs sm:text-sm font-medium text-[#6F6B68]">
                    ${formattedDate}
                </div>
            </div>
        `;
    }

    function renderDmodeYourDay(planData) {
        let contentHTML = '';

        if (planData.state === 'BRAND_NEW' || planData.state === 'NO_WORK_TODAY') {
            const tomorrowLine = planData.tomorrowTasksCount > 0
                ? `<p class="text-xs text-[#8C8782] font-medium pt-0.5">${window.t ? window.t('modes.urgent.nextScheduledWork', {}, 'Next planned work: Tomorrow') : 'Next planned work: Tomorrow'} (${planData.tomorrowTasksCount} ${window.t ? window.t('workspace.tasksCount', { count: planData.tomorrowTasksCount }, 'tasks') : 'tasks'})</p>`
                : '';

            contentHTML = `
                <div class="py-5 px-4 text-center space-y-2 bg-[#FAF8F5] rounded-xl border border-dashed border-[#E8E4E1]">
                    <p class="font-heading text-base font-bold text-[#202124]">${window.t ? window.t('modes.default.nothingPlannedToday', {}, 'Nothing planned for today.') : 'Nothing planned for today.'}</p>
                    <p class="text-xs sm:text-sm text-[#6F6B68] max-w-md mx-auto">${window.t ? window.t('modes.default.nothingPlannedSubtitle', {}, "You don't need to fill the space. Start with whatever matters today.") : "You don't need to fill the space. Start with whatever matters today."}</p>
                    ${tomorrowLine}
                    <div class="pt-1.5 flex items-center justify-center gap-2.5">
                        <button type="button" onclick="window.TempoMode.openPlanWorkspace()"
                                class="btn-primary px-4 py-2 rounded-xl text-xs font-bold transition shadow-xs cursor-pointer inline-flex items-center space-x-1.5">
                            <span>${window.t ? window.t('modes.default.addTask', {}, '+ Add a task') : '+ Add a task'}</span>
                        </button>
                        ${planData.hasActivePlan ? `
                            <button type="button" onclick="window.TempoMode.openPlanWorkspace()"
                                    class="px-4 py-2 rounded-xl text-xs font-semibold text-[#202124] bg-white border border-[#D5CEC8] hover:bg-stone-50 transition shadow-xs cursor-pointer">
                                ${window.t ? window.t('modes.default.viewMyPlan', {}, 'View my plan') : 'View my plan'}
                            </button>
                        ` : ''}
                    </div>
                </div>
            `;
        } else if (planData.state === 'TODAY_COMPLETE') {
            const tomorrowLine = planData.tomorrowTasksCount > 0
                ? `<p class="text-xs text-[#4A7C59] font-medium">${window.t ? window.t('modes.urgent.nextScheduledWork', {}, 'Next planned work: Tomorrow') : 'Next planned work: Tomorrow'}</p>`
                : '';

            const completedTasksHTML = planData.todayItems.map(pt => renderDmodeTaskRow(pt, false)).join('');

            contentHTML = `
                <div class="space-y-4">
                    <div class="py-4 px-4 text-center space-y-1.5 bg-[#EDF7F1] rounded-xl border border-[#CDE9DA]">
                        <p class="font-heading text-base font-bold text-[#166545]">✓ ${window.t ? window.t('modes.default.todayComplete', {}, "You're done with what was planned for today.") : "You're done with what was planned for today."}</p>
                        ${tomorrowLine}
                    </div>
                    <div class="space-y-2">
                        ${completedTasksHTML}
                    </div>
                </div>
            `;
        } else {
            // ACTIVE_TODAY: Sort (1) in-progress unfinished task, (2) remaining incomplete in planned order, (3) completed in planned order
            const inProgress = [];
            const upcoming = [];
            const completed = [];

            planData.todayItems.forEach(pt => {
                if (pt.task.completed) {
                    completed.push(pt);
                } else if (pt.task.isInProgress) {
                    inProgress.push(pt);
                } else {
                    upcoming.push(pt);
                }
            });

            const sortedItems = [...inProgress, ...upcoming, ...completed];
            contentHTML = `
                <div class="space-y-2.5">
                    ${sortedItems.map(pt => renderDmodeTaskRow(pt, true)).join('')}
                </div>
            `;
        }

        return `
            <div id="dmode-your-day" class="bg-white border border-[#E8E4E1] rounded-2xl p-5 sm:p-6 shadow-xs space-y-4">
                <div class="flex items-center justify-between">
                    <div class="space-y-0.5">
                        <div class="flex items-center space-x-2">
                            <h3 class="font-heading text-lg sm:text-xl font-extrabold text-[#202124]">
                                ${window.t ? window.t('modes.default.yourDay', {}, 'Your Day') : 'Your Day'}
                            </h3>
                            <span class="text-xs text-[#6F6B68] font-medium hidden sm:inline">• ${window.t ? window.t('modes.default.todaysPlannedWork', {}, "Today's planned work") : "Today's planned work"}</span>
                        </div>
                    </div>
                    <button type="button" 
                            onclick="window.TempoMode.openPlanWorkspace()" 
                            class="text-xs font-bold text-[#FF6B2C] hover:text-[#E05316] flex items-center space-x-1 transition cursor-pointer">
                        <span>${window.t ? window.t('modes.default.viewMyPlan', {}, 'View my plan') : 'View my plan'}</span>
                        <span>→</span>
                    </button>
                </div>
                ${contentHTML}
            </div>
        `;
    }

    function renderDmodeTaskRow(pt, showFocusActions = true) {
        const task = pt.task;
        const isCompleted = !!task.completed;
        const isInProgress = !isCompleted && !!task.isInProgress;
        const isExpanded = dmodeExpandedTaskIds.has(task.id);

        // Status Symbol Button
        let statusButtonHTML = '';
        if (isCompleted) {
            statusButtonHTML = `
                <button type="button" 
                        onclick="window.TempoMode.toggleDmodeTask('${task.id}', event)"
                        class="w-6 h-6 rounded-full bg-[#EDF7F1] text-[#166545] border border-[#CDE9DA] hover:bg-[#DDF0E5] flex items-center justify-center text-xs font-bold transition flex-shrink-0 cursor-pointer"
                        title="Mark as incomplete">
                    ✓
                </button>
            `;
        } else if (isInProgress) {
            statusButtonHTML = `
                <button type="button" 
                        onclick="window.TempoMode.toggleDmodeTask('${task.id}', event)"
                        class="w-6 h-6 rounded-full bg-[#FFE9DC] text-[#FF6B2C] border border-[#FFD2BA] hover:bg-[#FFD2BA] flex items-center justify-center text-xs font-bold transition flex-shrink-0 cursor-pointer"
                        title="Mark as complete">
                    ●
                </button>
            `;
        } else {
            statusButtonHTML = `
                <button type="button" 
                        onclick="window.TempoMode.toggleDmodeTask('${task.id}', event)"
                        class="w-6 h-6 rounded-full bg-white text-[#8C8782] hover:text-[#202124] border border-[#D5CEC8] hover:border-[#8C8782] flex items-center justify-center text-xs font-bold transition flex-shrink-0 cursor-pointer"
                        title="Mark as complete">
                    ○
                </button>
            `;
        }

        // Title styling
        const titleClass = isCompleted
            ? 'line-through text-[#8C8782]'
            : (isInProgress ? 'font-bold text-[#202124]' : 'font-semibold text-[#202124]');

        // Metadata: Planned time
        const timeStr = pt.scheduledStartTime ? formatTime12H(pt.scheduledStartTime) : (window.t ? window.t('modes.default.flexible', {}, 'Flexible') : 'Flexible');

        // Metadata: Estimate
        const durationStr = (task.durationMinutes && task.durationMinutes > 0)
            ? formatDurationMinutes(task.durationMinutes)
            : '';

        // Subtasks progress
        const subtasks = Array.isArray(task.subtasks) ? task.subtasks : [];
        let subtasksIndicatorHTML = '';
        if (subtasks.length > 0) {
            const doneCount = subtasks.filter(s => s.completed).length;
            subtasksIndicatorHTML = `
                <button type="button" 
                        onclick="window.TempoMode.toggleDmodeSubtasksExpanded('${task.id}', event)"
                        class="text-xs text-[#8C8782] hover:text-[#202124] flex items-center space-x-1 cursor-pointer transition">
                    <span>${doneCount} / ${subtasks.length} ${window.t ? window.t('modes.default.steps', {}, 'steps') : 'steps'}</span>
                    <span class="text-[9px] transform ${isExpanded ? 'rotate-180' : ''} transition-transform">▼</span>
                </button>
            `;
        }

        // Focus CTA Button
        let focusBtnHTML = '';
        if (showFocusActions && !isCompleted) {
            if (isInProgress) {
                focusBtnHTML = `
                    <button type="button" 
                            onclick="window.TempoMode.startDmodeTaskFocus('${task.id}')"
                            class="btn-primary px-3 py-1.5 rounded-lg text-xs font-bold shadow-xs inline-flex items-center space-x-1 transition cursor-pointer flex-shrink-0">
                        <span>${window.t ? window.t('modes.default.continue', {}, 'Continue') : 'Continue'}</span>
                        <span>→</span>
                    </button>
                `;
            } else {
                focusBtnHTML = `
                    <button type="button" 
                            onclick="window.TempoMode.startDmodeTaskFocus('${task.id}')"
                            class="text-xs font-semibold text-[#FF6B2C] hover:text-[#E05316] hover:bg-[#FFE9DC] px-2.5 py-1.5 rounded-lg transition inline-flex items-center space-x-1 cursor-pointer flex-shrink-0">
                        <span>${window.t ? window.t('modes.default.focus', {}, 'Focus') : 'Focus'}</span>
                        <span>→</span>
                    </button>
                `;
            }
        }

        // Subtasks expanded list
        let subtasksListHTML = '';
        if (isExpanded && subtasks.length > 0) {
            subtasksListHTML = `
                <div class="mt-2 pt-2 border-t border-[#F0ECE9] space-y-1.5 pl-8">
                    ${subtasks.map(sub => `
                        <div class="flex items-center space-x-2 py-0.5">
                            <button type="button" 
                                    onclick="window.TempoMode.toggleDmodeSubtask('${task.id}', '${sub.id}', event)"
                                    class="w-4 h-4 rounded text-[10px] font-bold border transition flex items-center justify-center cursor-pointer ${sub.completed ? 'bg-[#EDF7F1] border-[#CDE9DA] text-[#166545]' : 'bg-white border-[#D5CEC8] text-transparent hover:border-[#166545]'}">
                                ${sub.completed ? '✓' : ''}
                            </button>
                            <span class="text-xs ${sub.completed ? 'line-through text-[#8C8782]' : 'text-[#202124]'}">
                                ${escapeHTML(sub.title || sub.name)}
                            </span>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        return `
            <div class="bg-white border border-[#E8E4E1] hover:border-[#D5CEC8] rounded-xl p-3.5 sm:p-4 transition flex flex-col space-y-1.5">
                <div class="flex items-center justify-between gap-3">
                    <div class="flex items-center space-x-3 min-w-0 flex-1">
                        ${statusButtonHTML}
                        <div class="min-w-0 flex-1">
                            <div class="text-sm sm:text-base ${titleClass} truncate">
                                ${escapeHTML(task.name)}
                            </div>
                            <div class="flex flex-wrap items-center gap-x-2.5 gap-y-1 text-xs text-[#8C8782] pt-0.5">
                                <span>${timeStr}</span>
                                ${durationStr ? `<span>•</span><span>${durationStr}</span>` : ''}
                                ${subtasksIndicatorHTML ? `<span>•</span>${subtasksIndicatorHTML}` : ''}
                            </div>
                        </div>
                    </div>
                    ${focusBtnHTML}
                </div>
                ${subtasksListHTML}
            </div>
        `;
    }

    function renderDmodeTools() {
        if (window.TempoTools && typeof window.TempoTools.renderSectionHTML === 'function') {
            return `<div id="dmode-tempo-tools-container">${window.TempoTools.renderSectionHTML()}</div>`;
        }
        return '';
    }

    function renderDmodeSelfCheckCard() {
        if (!window.TempoRecoverySelfCheck || typeof window.TempoRecoverySelfCheck.getState !== 'function') {
            return '';
        }

        const state = window.TempoRecoverySelfCheck.getState();
        if (!state) return '';

        // State A: No trackers
        if (state.type === 'STATE_A') {
            return `
                <div class="bg-white border border-[#E8E4E1] rounded-2xl p-5 sm:p-6 shadow-xs space-y-3">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-2">
                            <span class="text-base text-[#166545]">🌱</span>
                            <h4 class="font-heading text-base font-bold text-[#202124]">Self-check</h4>
                        </div>
                    </div>
                    <p class="text-xs sm:text-sm text-[#6F6B68]">Keep an eye on the things that matter to you over time.</p>
                    <div class="pt-1">
                        <button type="button" 
                                onclick="window.TempoMode.openStrack('setup');"
                                class="px-4 py-2 rounded-xl text-xs sm:text-sm font-bold text-[#166545] bg-[#EDF7F1] hover:bg-[#DDF0E5] border border-[#CDE9DA] inline-flex items-center space-x-1.5 transition cursor-pointer">
                            <span>Set up my Self-check</span>
                            <span>→</span>
                        </button>
                    </div>
                </div>
            `;
        }

        // State B: Trackers exist, today uncompleted
        if (state.type === 'STATE_B') {
            const trackersCount = state.trackersCount || 0;
            const streakText = (state.streak && state.streak > 0)
                ? `<span class="text-xs text-[#8C8782] font-medium">• ${state.streak}-day check-in streak</span>`
                : '';

            return `
                <div class="bg-white border border-[#E8E4E1] rounded-2xl p-5 sm:p-6 shadow-xs space-y-4">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-2">
                            <span class="text-base text-[#166545]">🌱</span>
                            <h4 class="font-heading text-base font-bold text-[#202124]">Self-check</h4>
                            ${streakText}
                        </div>
                    </div>
                    <div class="space-y-1">
                        <p class="font-heading text-base font-bold text-[#202124]">How have things been today?</p>
                        <p class="text-xs sm:text-sm text-[#6F6B68]">${trackersCount} thing${trackersCount === 1 ? '' : 's'} you're keeping an eye on</p>
                    </div>
                    <div class="flex items-center space-x-3 pt-1">
                        <button type="button" 
                                onclick="window.TempoMode.openStrack('checkin');"
                                class="btn-primary px-4 py-2 rounded-xl text-xs sm:text-sm font-bold shadow-xs inline-flex items-center space-x-1.5 transition cursor-pointer">
                            <span>Check in</span>
                            <span>→</span>
                        </button>
                        <button type="button" 
                                onclick="window.TempoMode.openStrack('manage');"
                                class="px-3.5 py-2 rounded-xl text-xs sm:text-sm font-medium text-[#6F6B68] hover:text-[#202124] hover:bg-stone-50 transition cursor-pointer">
                            Manage
                        </button>
                    </div>
                </div>
            `;
        }

        // State C: Checked in today
        if (state.type === 'STATE_C') {
            const checkedCount = state.checkedCount || 0;
            const totalCount = state.totalCount || 0;
            const streakText = (state.streak && state.streak > 0)
                ? `<span class="text-xs text-[#8C8782] font-medium">• ${state.streak}-day check-in streak</span>`
                : '';

            return `
                <div class="bg-white border border-[#E8E4E1] rounded-2xl p-5 sm:p-6 shadow-xs space-y-4">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-2">
                            <span class="text-base text-[#166545]">🌱</span>
                            <h4 class="font-heading text-base font-bold text-[#202124]">Self-check</h4>
                            ${streakText}
                        </div>
                    </div>
                    <div class="space-y-1">
                        <p class="font-heading text-base font-bold text-[#166545]">✓ Checked in today</p>
                        <p class="text-xs sm:text-sm text-[#6F6B68]">${checkedCount} of ${totalCount} answered</p>
                    </div>
                    <div class="pt-1">
                        <button type="button" 
                                onclick="window.TempoMode.openStrack('view');"
                                class="px-4 py-2 rounded-xl text-xs sm:text-sm font-bold text-[#166545] bg-[#EDF7F1] hover:bg-[#DDF0E5] border border-[#CDE9DA] inline-flex items-center space-x-1.5 transition cursor-pointer">
                            <span>View / Edit</span>
                            <span>→</span>
                        </button>
                    </div>
                </div>
            `;
        }

        return '';
    }

    function renderDmodeContextualCard() {
        if (!window.TempoWeeklyReview || typeof window.TempoWeeklyReview.isReady !== 'function') {
            return '';
        }

        const isReady = window.TempoWeeklyReview.isReady();
        if (!isReady) return '';

        const week = (typeof window.TempoWeeklyReview.getLatestEligibleWeek === 'function')
            ? window.TempoWeeklyReview.getLatestEligibleWeek()
            : null;

        let daysText = 'Your weekly reflection is ready.';
        if (week && typeof window.TempoWeeklyReview.deriveRecap === 'function') {
            const recap = window.TempoWeeklyReview.deriveRecap(week.start, week.end);
            if (recap && recap.checkinsCount) {
                daysText = `You checked in on ${recap.checkinsCount} day${recap.checkinsCount === 1 ? '' : 's'} this week.`;
            }
        }

        const weekStartParam = week ? week.start : '';

        return `
            <div class="bg-gradient-to-r from-[#FFFBF7] to-[#FAF8F5] border border-[#F0ECE9] rounded-2xl p-5 sm:p-6 shadow-xs space-y-3">
                <div class="flex items-center justify-between">
                    <span class="text-[11px] font-extrabold uppercase tracking-wider text-[#FF6B2C]">YOUR WEEK IS READY</span>
                    <button type="button" 
                            onclick="if (window.TempoWeeklyReview && window.TempoWeeklyReview.snoozeOrDismissNotice) { window.TempoWeeklyReview.snoozeOrDismissNotice('${weekStartParam}'); window.TempoMode.renderActiveModeHome(); }"
                            class="text-xs text-[#8C8782] hover:text-[#202124] transition cursor-pointer"
                            title="Dismiss for now">
                        ✕
                    </button>
                </div>
                <p class="text-sm sm:text-base font-semibold text-[#202124]">${daysText}</p>
                <div class="pt-1">
                    <button type="button" 
                            onclick="if (window.TempoWeeklyReview) window.TempoWeeklyReview.open('${weekStartParam}');"
                            class="btn-primary px-4 py-2 rounded-xl text-xs sm:text-sm font-bold shadow-xs inline-flex items-center space-x-1.5 transition cursor-pointer">
                        <span>Look back at my week</span>
                        <span>→</span>
                    </button>
                </div>
            </div>
        `;
    }

    function renderDmodePostsSection() {
        return `
            <div class="space-y-4 pt-2">
                <!-- Header -->
                <div class="flex items-center justify-between">
                    <div class="space-y-0.5">
                        <div class="flex items-center space-x-2">
                            <h3 class="font-heading text-lg sm:text-xl font-extrabold text-[#202124]">
                                Tempo Posts
                            </h3>
                            <span class="text-xs text-[#6F6B68] font-medium hidden sm:inline">• A little something for when you have space.</span>
                        </div>
                        <p class="text-xs text-[#6F6B68] sm:hidden">A little something for when you have space.</p>
                    </div>
                    <button type="button" 
                            id="btn-see-all-posts"
                            onclick="if (window.TempoCommunity) { window.TempoCommunity.openCommunityModal(); }" 
                            class="text-xs font-bold text-[#FF6B2C] hover:text-[#E05316] flex items-center space-x-1 transition cursor-pointer">
                        <span>Xem tất cả bài viết</span>
                        <span>→</span>
                    </button>
                </div>

                <!-- Social Post Previews Container -->
                <div id="homepage-community-posts-list" class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <!-- Populated by window.TempoCommunity.renderHomepagePreview() -->
                </div>
            </div>
        `;
    }

    function renderDmodeLearnSolve() {
        if (window.TempoLearnSolve && typeof window.TempoLearnSolve.renderSectionHTML === 'function') {
            return `<div id="dmode-learn-solve-container">${window.TempoLearnSolve.renderSectionHTML()}</div>`;
        }
        return '';
    }

    function renderDmodeModeSwitchEntry() {
        return `
            <div id="dmode-mode-switch-bar" class="flex items-center justify-between px-4 py-2.5 bg-[#FAF8F5] border border-[#EAE4DF] rounded-2xl text-xs text-[#6F6B68]">
                <div class="flex items-center space-x-2">
                    <span class="text-stone-400">🧭</span>
                    <span class="font-medium text-[#202124]">${window.t ? window.t('modes.default.needDifferentSupport', {}, 'Need a different kind of support?') : 'Need a different kind of support?'}</span>
                </div>
                <button type="button" 
                        onclick="window.TempoMode.openChangeModeModal()" 
                        class="font-bold text-[#FF6B2C] hover:text-[#B83D08] flex items-center space-x-1 transition cursor-pointer">
                    <span>${window.t ? window.t('modes.selector.switchMode', {}, 'Change mode') : 'Change mode'}</span>
                    <span>→</span>
                </button>
            </div>
        `;
    }

    function renderDmodeGuestInvitation() {
        return `
            <div id="dmode-guest-invitation" class="p-4 sm:p-5 bg-gradient-to-r from-[#FFFBF7] to-[#FAF8F5] border border-[#EAE4DF] rounded-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
                <div class="space-y-1">
                    <span class="font-bold text-[#202124] text-sm">${window.t ? window.t('modes.default.guestSaveProgressTitle', {}, 'Save your progress across sessions') : 'Save your progress across sessions'}</span>
                    <p class="text-[#6F6B68]">${window.t ? window.t('modes.default.guestSaveProgressDesc', {}, 'Create a free account to plan your days, track habits, and preserve your work.') : 'Create a free account to plan your days, track habits, and preserve your work.'}</p>
                </div>
                <button type="button" onclick="if (window.TempoAuth) window.TempoAuth.openSignUpModal();"
                        class="btn-primary px-4 py-2 rounded-xl font-bold text-xs shrink-0 self-start sm:self-auto shadow-xs transition cursor-pointer">
                    ${window.t ? window.t('common.register', {}, 'Create free account') : 'Create free account'} →
                </button>
            </div>
        `;
    }

    function renderAssetPlaceholder(title, subtitle = '', sizeClass = 'w-24 h-24 sm:w-28 sm:h-24', isWhiteTheme = false) {
        const borderClass = isWhiteTheme ? 'border-white/50 bg-white/20 text-white' : 'border-[#202124]/20 bg-white/50 text-[#202124]';
        const badgeBg = isWhiteTheme ? 'bg-white/30 text-white' : 'bg-white/80 text-[#202124]/70';
        const textClass = isWhiteTheme ? 'text-white' : 'text-[#202124]/80';
        const subtextClass = isWhiteTheme ? 'text-white/85' : 'text-[#202124]/55';

        return `
            <div class="${sizeClass} rounded-2xl border-2 border-dashed ${borderClass} flex flex-col items-center justify-center p-2 text-center shrink-0 select-none shadow-2xs" 
                 title="Illustration Placeholder: ${title}">
                <div class="w-6 h-6 rounded-full ${badgeBg} flex items-center justify-center text-xs mb-1 shadow-2xs">
                    🌱
                </div>
                <span class="text-[10px] font-bold ${textClass} leading-tight">${title}</span>
                ${subtitle ? `<span class="text-[8px] ${subtextClass} leading-tight mt-0.5">${subtitle}</span>` : ''}
            </div>
        `;
    }

    function escapeHtml(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function renderQuickReliefCardHTML(extraClass = '') {
        const widthClass = extraClass ? ` ${extraClass}` : '';
        const titleText = (window.t ? window.t('modes.urgent.quickRelief') : null) || (isViLocale() ? 'Thư giãn' : 'Quick Relief');
        return `
            <div onclick="if (window.TempoStressRelief && window.TempoStressRelief.openModal) { window.TempoStressRelief.openModal('all', { context: 'recovery' }); } else if (window.TempoTriage && window.TempoTriage.openQuickReliefModal) { window.TempoTriage.openQuickReliefModal(); }"
                 role="button"
                 tabindex="0"
                 aria-label="${titleText}"
                 onkeydown="if(event.key==='Enter'||event.key===' ') { event.preventDefault(); this.click(); }"
                 class="bg-[#DEECE5] border border-[#728F83]/30 rounded-3xl px-2.5 py-3.5 sm:px-2 sm:py-4 flex items-center justify-center shadow-xs hover:shadow-md transition cursor-pointer group relative overflow-visible recovery-card-quick-relief shrink-0${widthClass}"
                 style="width: 334.92px; min-width: 334.92px; max-width: 334.92px; height: 100px; min-height: 100px; max-height: 100px; box-sizing: border-box; flex-shrink: 0; margin: 0;"
                 title="${titleText}">
                <div class="flex items-center justify-center gap-2 sm:gap-2.5" style="transform: translateX(10px);">
                    <div class="z-10 shrink-0">
                        <h3 class="text-2xl sm:text-[26px] font-bold text-[#6D8A7E] leading-tight whitespace-nowrap">
                            ${titleText}
                        </h3>
                    </div>
                    <img src="assets/quick-relief-mascot-transparent.png"
                         alt="${titleText}"
                         class="h-24 sm:h-28 w-auto object-contain shrink-0 select-none pointer-events-none group-hover:scale-105 transition-transform" />
                </div>
            </div>
        `;
    }

    function renderFocusNowCardHTML(extraClass = '') {
        const widthClass = extraClass ? ` ${extraClass}` : '';
        const titleText = (window.t ? window.t('modes.urgent.focusNow') : null) || (isViLocale() ? 'Tập trung' : 'Focus Now');
        return `
            <div onclick="if (window.TempoFocusZone && typeof window.TempoFocusZone.openQuickEntry === 'function') { window.TempoFocusZone.openQuickEntry(); } else if (window.TempoFocusZone && typeof window.TempoFocusZone.open === 'function') { window.TempoFocusZone.open(); } else if (window.TempoTriage && typeof window.TempoTriage.launchFocusMode === 'function') { window.TempoTriage.launchFocusMode(); }"
                 role="button"
                 tabindex="0"
                 aria-label="${titleText}"
                 onkeydown="if(event.key==='Enter'||event.key===' ') { event.preventDefault(); this.click(); }"
                 class="bg-[#D29C85] border border-[#4A4541]/20 rounded-3xl px-2.5 py-3.5 sm:px-2 sm:py-4 flex items-center justify-center shadow-xs hover:shadow-md transition cursor-pointer group relative overflow-visible recovery-support-focus-now shrink-0${widthClass}"
                 style="width: 334.92px; min-width: 334.92px; max-width: 334.92px; height: 100px; min-height: 100px; max-height: 100px; box-sizing: border-box; flex-shrink: 0; margin: 0;"
                 title="${titleText}">
                <div class="flex items-center justify-center gap-2 sm:gap-2.5" style="transform: translateX(-10px);">
                    <img src="assets/focus-now-mascot.png"
                         alt="${titleText}"
                         class="h-24 sm:h-28 w-auto object-contain shrink-0 select-none pointer-events-none group-hover:scale-105 transition-transform" />
                    <div class="z-10 shrink-0">
                        <h3 class="text-2xl sm:text-[26px] font-bold text-white leading-tight whitespace-nowrap">
                            ${titleText}
                        </h3>
                    </div>
                </div>
            </div>
        `;
    }


    function renderLearnSolveCardHTML(extraClass = '') {
        const widthClass = extraClass ? ` ${extraClass}` : '';
        return `
            <div onclick="if (window.TempoApp) { window.TempoApp.navigateTo('community', 'tips'); } else { window.location.hash = '#community?tab=tips'; }"
                 class="bg-[#FBEDD9] border border-[#736F68] rounded-3xl overflow-hidden p-4 sm:p-5 flex items-center justify-between min-h-[175px] h-[175px]${widthClass} shadow-xs hover:shadow-md transition cursor-pointer group relative"
                 title="Learn & Solve">
                <div class="relative z-10 flex-1 min-w-0 pr-1">
                    <h3 class="text-[22px] sm:text-[25px] font-bold text-[#736F68] mb-1 group-hover:text-[#5B5751] transition leading-tight whitespace-nowrap">
                        Learn &amp; Solve
                    </h3>
                    <p class="text-[14px] sm:text-[16px] text-[#736F68] leading-[1.35] max-w-[155px]">
                        Tips and tools to help you cope.
                    </p>
                </div>
                <img src="assets/learn-solve-mascot.png"
                     alt="Learn & Solve Mascot"
                     class="h-[105px] w-auto object-contain shrink-0 select-none pointer-events-none -mr-1 sm:-mr-2 translate-y-1" />
            </div>
        `;
    }

    function renderCommunityPreviewsHTML(previewPosts) {
        if (!Array.isArray(previewPosts) || previewPosts.length === 0) {
            return `
                <div class="h-48 flex flex-col items-center justify-center text-center p-6 space-y-2 text-[#8E8A85]">
                    <img src="assets/comment_action_symbol.png" alt="No posts" class="w-6 h-6 opacity-40 object-contain mb-0.5">
                    <p class="text-xs font-bold text-[#5A5550]">${isViLocale() ? 'Chưa có bài viết cộng đồng nào' : 'No community posts yet'}</p>
                    <p class="text-[10.5px] text-[#8E8A85] leading-relaxed">${isViLocale() ? 'Hãy là người đầu tiên chia sẻ với bạn bè trong cộng đồng.' : 'Be the first to share with your peers in the community.'}</p>
                </div>
            `;
        }

        return previewPosts.slice(0, 2).map(post => {
            const tagsHTML = (post.tags || []).map(t => `
                <span class="px-3 py-0.5 rounded-full text-xs font-semibold ${t.bg} ${t.text}">
                    ${escapeHtml(t.label)}
                </span>
            `).join(' ');

            const commentsCount = (post.comments && post.comments.length > 0) ? post.comments.length : (post.commentsCount || 0);

            return `
                <div onclick="window.TempoApp.navigateTo('community'); if(window.TempoCommunity) { window.TempoCommunity.selectTab('posts'); setTimeout(() => { const el = document.querySelector('[data-post-id=\'${post.id}\']'); if(el) el.scrollIntoView({ behavior: 'smooth', block: 'center' }); }, 150); }"
                     class="bg-[#F6F0EB] border border-[#4A4541] rounded-2xl sm:rounded-3xl p-4 sm:p-[18px] space-y-2.5 shadow-xs hover:border-[#DE8662] transition cursor-pointer group"
                     title="Open post by ${escapeHtml(post.authorName)}">
                    <!-- Header -->
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-2.5">
                            <img src="${escapeHtml(post.avatar)}" alt="${escapeHtml(post.authorName)}" class="w-9 h-9 rounded-full object-cover">
                            <div>
                                <h4 class="text-sm font-bold text-[#202124] leading-tight">${escapeHtml(post.authorName)}</h4>
                                <span class="text-xs text-[#8E8A85]">${escapeHtml((window.TempoI18n && typeof window.TempoI18n.formatTimeAgo === 'function') ? window.TempoI18n.formatTimeAgo(post.timeAgo || 'Recent') : (post.timeAgo || 'Recent'))}</span>
                            </div>
                        </div>
                        <div class="flex items-center space-x-2">
                            ${tagsHTML}
                            <div class="p-1 text-[#4A4541] hover:text-[#DE8662]">
                                <img src="assets/bookmark_action_symbol.png" alt="Bookmark" class="w-4 h-4 object-contain opacity-70">
                            </div>
                        </div>
                    </div>

                    <!-- Content -->
                    <p class="text-xs sm:text-[13px] text-[#202124] leading-relaxed">
                        ${escapeHtml(post.content)}
                    </p>

                    <!-- Thumbnails if present -->
                    ${(post.thumbnails && post.thumbnails.length > 0) ? `
                        <div class="grid grid-cols-4 gap-2 pt-1">
                            ${post.thumbnails.slice(0, 4).map(img => `
                                <div class="aspect-4/3 rounded-xl overflow-hidden bg-stone-100 border border-stone-200">
                                    <img src="${escapeHtml(img)}" alt="Attachment" class="w-full h-full object-cover">
                                </div>
                            `).join('')}
                        </div>
                    ` : ''}

                    <!-- Action stats row matching Reference Screenshot -->
                    <div class="flex items-center space-x-5 text-[#4A4541] text-xs pt-1">
                        <span class="flex items-center space-x-1.5">
                            <span class="text-sm">♡</span>
                            <span>${post.likes || 0}</span>
                        </span>
                        <span class="flex items-center space-x-1.5">
                            <img src="assets/comment_action_symbol.png" alt="Comments" class="w-3.5 h-3.5 object-contain">
                            <span>${commentsCount}</span>
                        </span>
                        <span class="flex items-center space-x-1.5">
                            <img src="assets/message_action_symbol.png" alt="Share" class="w-3.5 h-3.5 object-contain">
                        </span>
                    </div>
                </div>
            `;
        }).join('');
    }

    function renderEntryQuickReliefCardHTML() {
        const titleText = (window.t ? window.t('modes.default.quickRelief') : null) || (isViLocale() ? 'Thư giãn' : 'Quick Relief');
        return `
            <div onclick="if (window.TempoStressRelief && window.TempoStressRelief.openModal) { window.TempoStressRelief.openModal(); } else if (window.TempoTriage && window.TempoTriage.openQuickReliefModal) { window.TempoTriage.openQuickReliefModal(); }"
                 role="button"
                 tabindex="0"
                 aria-label="${titleText}"
                 onkeydown="if(event.key==='Enter'||event.key===' ') { event.preventDefault(); this.click(); }"
                 class="bg-[#DEECE5] border border-[#728F83]/30 rounded-3xl p-3.5 sm:p-4 flex items-center justify-center gap-2 sm:gap-2.5 h-[100px] shadow-xs hover:shadow-md transition cursor-pointer group relative overflow-hidden"
                 title="${titleText}">
                <div class="z-10 shrink-0">
                    <h3 class="text-2xl sm:text-[26px] font-bold text-[#6D8A7E] leading-tight whitespace-nowrap">
                        ${titleText}
                    </h3>
                </div>
                <img src="assets/quick-relief-mascot-transparent.png"
                     alt="${titleText}"
                     class="h-[102px] w-auto object-contain shrink-0 select-none pointer-events-none group-hover:scale-105 transition-transform" />
            </div>
        `;
    }

    function renderEntryFocusNowCardHTML() {
        const titleText = (window.t ? window.t('modes.default.focusNow') : null) || (isViLocale() ? 'Tập trung' : 'Focus Now');
        return `
            <div onclick="if (window.TempoFocusZone && window.TempoFocusZone.openQuickEntry) { window.TempoFocusZone.openQuickEntry(); } else if (window.TempoTriage && window.TempoTriage.launchFocusMode) { window.TempoTriage.launchFocusMode(); }"
                 role="button"
                 tabindex="0"
                 aria-label="${titleText}"
                 onkeydown="if(event.key==='Enter'||event.key===' ') { event.preventDefault(); this.click(); }"
                 class="bg-[#D29C85] border border-[#4A4541]/20 rounded-3xl p-3.5 sm:p-4 flex items-center justify-center h-[100px] shadow-xs hover:shadow-md transition cursor-pointer group relative overflow-hidden"
                 title="${titleText}">
                <div class="flex items-center justify-center gap-2 sm:gap-2.5" style="transform: translateX(-10px);">
                    <img src="assets/focus-now-mascot.png"
                         alt="${titleText}"
                         class="h-[102px] w-auto object-contain shrink-0 select-none pointer-events-none group-hover:scale-105 transition-transform" />
                    <div class="z-10 shrink-0">
                        <h3 class="text-2xl sm:text-[26px] font-bold text-white leading-tight whitespace-nowrap">
                            ${titleText}
                        </h3>
                    </div>
                </div>
            </div>
        `;
    }


    /**
     * REDESIGNED TEMPO ENTRYHOME
     * Restored to exact visual hierarchy matching reference screenshot media_1792935418362_1094ad43.png
     */
    function renderEntryHomeHTML() {
        let posts = (window.TempoCommunity && typeof window.TempoCommunity.getAllPosts === 'function')
            ? window.TempoCommunity.getAllPosts()
            : [];
        if (!Array.isArray(posts) || posts.length === 0) {
            if (window.TempoCommunity && typeof window.TempoCommunity.getInitialPosts === 'function') {
                posts = window.TempoCommunity.getInitialPosts();
            }
        }
        const previewPosts = (Array.isArray(posts) && posts.length > 0) ? posts.slice(0, 2) : [];

        return `
            <div class="max-w-6xl mx-auto py-2 sm:py-4 space-y-7 sm:space-y-9 font-arimo" data-tempo-ui="entry-home">
                <!-- ==============================================================
                     UPPER SECTION: DESKTOP 2-COLUMN (LEFT: WELCOME + ACTIONS; RIGHT: COMMUNITY)
                     Matches exact Reference Screenshot media_1792935418362_1094ad43.png
                     ============================================================== -->
                <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 sm:gap-7 items-stretch">
                    <!-- LEFT COLUMN (approx 58-60% width): Welcome Card + 2 Primary Action Cards -->
                    <div class="lg:col-span-7 flex flex-col justify-start space-y-5">
                        <!-- Welcome / Hero Card (Proportional, comfortable spacing matching reference) -->
                        <div class="bg-[#FEFAF4] border border-[#EAE4DF] rounded-3xl sm:rounded-[32px] p-6 sm:p-6.5 sm:pb-7 shadow-[0_4px_20px_rgba(74,69,65,0.06)] flex flex-col justify-between flex-none lg:h-[277.22px] min-h-[180px] sm:min-h-[195px] relative" data-tempo-ui="entry-welcome-card">
                            <div class="lg:translate-y-[10px]">
                                <span class="text-[19px] sm:text-[21px] font-bold text-[#D99E87] block tracking-wide">
                                    ${(window.t ? window.t('modes.default.welcomeEyebrow') : null) || (isViLocale() ? 'Chào mừng đến với Tempo' : 'Welcome to Tempo')}
                                </span>
                            </div>

                            <div class="my-auto lg:translate-y-[3.5px] py-1">
                                <h1 class="text-[30px] sm:text-[36px] lg:text-[42px] font-bold text-[#726D69] tracking-[-0.035em] leading-[1.15] lg:whitespace-nowrap">
                                    ${(window.t ? window.t('modes.default.whatDoYouNeed') : null) || (isViLocale() ? 'Bạn cần gì ngay lúc này?' : 'What do you need right now?')}
                                </h1>
                            </div>

                            <div class="pt-1">
                                <button type="button"
                                        id="btn-hero-figure-start"
                                        onclick="if (window.TempoApp && typeof window.TempoApp.openRoutingModal === 'function') { window.TempoApp.openRoutingModal(); } else if (window.TempoMode && typeof window.TempoMode.openHelpSelectionModal === 'function') { window.TempoMode.openHelpSelectionModal(); } else { const m = document.getElementById('modal-routing-selection'); if (m) { m.classList.remove('hidden'); document.body.classList.add('overflow-hidden'); } }"
                                        class="px-6 py-3 rounded-2xl bg-[#D28C74] hover:bg-[#C27C64] text-white font-bold text-sm sm:text-base shadow-xs transition inline-flex items-center space-x-2 cursor-pointer group">
                                    <span>${(window.t ? window.t('modes.default.helpMeStart') : null) || (isViLocale() ? 'Giúp tôi tìm hướng bắt đầu' : 'Help me figure out where to start')}</span>
                                    <span class="group-hover:translate-x-1 transition-transform">→</span>
                                </button>
                            </div>
                        </div>

                        <!-- 2x2 Card Group (Top Row: Quick Relief & Focus Now; Bottom Row: Self-check & Work Plan) -->
                        <!-- Top Row: Quick Relief & Focus Now -->
                        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-5 sm:max-w-[600.33px] lg:w-[600.33px] mx-auto" data-tempo-ui="entry-action-cards">
                            <!-- Action Card 1: Quick Relief (Simplified without subtext) -->
                            ${renderEntryQuickReliefCardHTML()}

                            <!-- Action Card 2: Focus Now (Simplified without subtext) -->
                            ${renderEntryFocusNowCardHTML()}
                        </div>

                        <!-- Bottom Row: Self-check & Work Plan (Exact 20px vertical gap, centered relative to Welcome Card) -->
                        <div class="grid grid-cols-1 sm:grid-cols-2 gap-6 sm:gap-7 max-w-full sm:max-w-[608.66px] mx-auto entry-bottom-row-desktop" data-tempo-ui="entry-secondary-cards">
                            <!-- Card 1: Self-check (Soft Sage) -->
                            <div onclick="if (window.TempoMode && typeof window.TempoMode.openStrack === 'function') { window.TempoMode.openStrack('open', { sourceContext: 'entry' }); } else if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') { window.TempoApp.navigateTo('stress-check'); } else { window.location.hash = '#stress-check'; }"
                                 role="button"
                                 tabindex="0"
                                 aria-label="Self-check"
                                 onkeydown="if(event.key==='Enter'||event.key===' ') { event.preventDefault(); this.click(); }"
                                 class="bg-[#DEECE5] border border-[#728F83]/20 rounded-3xl sm:rounded-[28px] h-[185px] sm:h-[165px] p-2 flex items-center justify-center shadow-xs hover:shadow-md hover:scale-[1.01] transition cursor-pointer relative group overflow-hidden"
                                 title="Self-check: Check in with your stress levels">
                                <img src="assets/self-check-mascot.png"
                                     alt="Self-check"
                                     class="h-32 sm:h-36 w-auto object-contain select-none pointer-events-none group-hover:scale-105 transition-transform" />
                            </div>

                            <!-- Card 2: Work Plan (Soft Peach) -->
                            <div onclick="if (window.TempoApp) window.TempoApp.navigateTo('plan-workspace'); else window.location.hash = '#plan-workspace';"
                                 role="button"
                                 tabindex="0"
                                 aria-label="Work Plan"
                                 onkeydown="if(event.key==='Enter'||event.key===' ') { event.preventDefault(); this.click(); }"
                                 class="bg-[#FBE9DF] border border-[#F0D5CC]/40 rounded-3xl sm:rounded-[28px] h-[185px] sm:h-[165px] p-2 flex items-center justify-center shadow-xs hover:shadow-md hover:scale-[1.01] transition cursor-pointer relative group overflow-hidden"
                                 title="Work Plan: Organize tasks and manage deadlines">
                                <img src="assets/work-plan-mascot.png"
                                     alt="Work Plan"
                                     class="h-32 sm:h-36 w-auto object-contain select-none pointer-events-none group-hover:scale-105 transition-transform" />
                            </div>
                        </div>
                    </div>

                    <!-- RIGHT COLUMN (approx 40-42% width): Từ Cộng đồng Tempo -->
                    <div class="lg:col-span-5 flex flex-col items-start justify-start">
                        <div class="bg-[#FEFAF4] border border-[#EAE4DF] rounded-3xl sm:rounded-[32px] p-4.5 sm:p-5 shadow-xs flex flex-col justify-between w-full lg:w-[447.15px] lg:h-[541.23px] space-y-3.5" data-tempo-ui="entry-community-panel">
                            <!-- Header -->
                            <div class="flex items-center justify-between pb-0.5 w-full">
                                <div class="flex items-center space-x-2.5">
                                    <div class="w-8 h-8 rounded-full bg-[#F6E6DE] flex items-center justify-center shrink-0">
                                        <img src="assets/comment_action_symbol.png" alt="Community" class="w-4 h-4 object-contain" />
                                    </div>
                                    <h3 class="font-bold text-base sm:text-lg text-[#55504C] tracking-tight">
                                        ${(window.t ? window.t('modes.default.fromCommunity') : null) || (isViLocale() ? 'Cộng đồng Tempo' : 'From the Tempo Community')}
                                    </h3>
                                </div>
                                <button type="button"
                                        id="btn-see-all-posts"
                                        onclick="window.TempoApp.navigateTo('community'); if(window.TempoCommunity) window.TempoCommunity.selectTab('posts');"
                                        class="px-3.5 py-1 rounded-full bg-[#FCEFE8] hover:bg-[#F8E1D5] text-[#DE8662] text-xs font-bold transition flex items-center space-x-1 cursor-pointer"
                                        aria-label="${isViLocale() ? 'Xem tất cả →' : 'View all →'}" title="${isViLocale() ? 'Xem tất cả →' : 'View all →'}">
                                    <span>${(window.t ? (window.t('modes.default.viewAll') || window.t('modes.default.seeAll')) : null) || (isViLocale() ? 'Xem tất cả' : 'View all')}</span>
                                    <span>→</span>
                                </button>
                            </div>

                            <!-- Community Previews Container -->
                            <div id="homepage-community-posts-list" class="space-y-3 flex-1 flex flex-col justify-between w-full">
                                ${renderCommunityPreviewsHTML(previewPosts)}
                            </div>
                        </div>
                    
                </div>
                <style>
                @media (min-width: 1024px) {
                    .entry-bottom-row-desktop {
                        width: 608.65625px !important;
                        max-width: none !important;
                        margin-left: calc((100% - 608.65625px) / 2) !important;
                        margin-right: calc((100% - 608.65625px) / 2) !important;
                    }
                }
                </style>
            </div>
        `;
    }

    function renderDmodeHome() {
        applyModeVisibility(MODES.DEFAULT);

        const dmodeBox = document.getElementById('dmode-home-content');
        if (!dmodeBox) return;

        dmodeBox.innerHTML = renderEntryHomeHTML();

        if (window.TempoCommunity && typeof window.TempoCommunity.renderHomepagePreview === 'function') {
            window.TempoCommunity.renderHomepagePreview();
        }
    }

    const renderEntryHome = renderDmodeHome;

    function toggleDmodeTask(taskId, e) {
        if (e && e.stopPropagation) e.stopPropagation();
        let isNowCompleted = false;

        if (window.TempoPlanWorkspace && typeof window.TempoPlanWorkspace.toggleTaskComplete === 'function') {
            window.TempoPlanWorkspace.toggleTaskComplete(taskId, e);
            const plan = window.TempoPlanWorkspace.getActivePlan();
            const pt = plan?.plannedTasks?.find(item => item.task && item.task.id === taskId);
            if (pt && pt.task) isNowCompleted = pt.task.completed;
        } else if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.toggleTaskCompleted === 'function') {
            isNowCompleted = window.TempoEmergencyFlow.toggleTaskCompleted(taskId);
        } else if (window.TempoPlanStore && typeof window.TempoPlanStore.getActivePlan === 'function') {
            const plan = window.TempoPlanStore.getActivePlan('emergency');
            const ptItem = plan?.plannedTasks?.find(pt => pt.task && pt.task.id === taskId);
            if (ptItem && ptItem.task) {
                ptItem.task.completed = !ptItem.task.completed;
                if (ptItem.task.completed) ptItem.task.isInProgress = false;
                window.TempoPlanStore.updateTaskState(taskId, {
                    completed: ptItem.task.completed,
                    isInProgress: ptItem.task.isInProgress
                });
                isNowCompleted = ptItem.task.completed;
            }
        }

        if (isNowCompleted && window.TempoApp) {
            window.TempoApp.triggerConfetti();
            window.TempoApp.showToast("Task completed! Taking small steps protects your momentum.");
        }

        renderActiveModeHome();
    }

    function toggleDmodeSubtask(taskId, subtaskId, e) {
        if (e && e.stopPropagation) e.stopPropagation();
        const plan = (window.TempoPlanStore && window.TempoPlanStore.getActivePlan) ? window.TempoPlanStore.getActivePlan('emergency') : null;
        let isDone = true;
        if (plan) {
            let task = null;
            if (Array.isArray(plan.plannedTasks)) {
                const pt = plan.plannedTasks.find(item => item.task && String(item.task.id) === String(taskId));
                if (pt) task = pt.task;
            }
            if (!task && Array.isArray(plan.tasks)) {
                task = plan.tasks.find(t => String(t.id) === String(taskId));
            }
            if (task && Array.isArray(task.subtasks)) {
                const sub = task.subtasks.find(s => String(s.id) === String(subtaskId));
                if (sub) isDone = !sub.completed;
            }
        }
        setSubtaskCompleted(taskId, subtaskId, isDone);
    }

    function toggleDmodeSubtasksExpanded(taskId, e) {
        if (e && e.stopPropagation) e.stopPropagation();
        if (dmodeExpandedTaskIds.has(taskId)) {
            dmodeExpandedTaskIds.delete(taskId);
        } else {
            dmodeExpandedTaskIds.add(taskId);
        }
        renderActiveModeHome();
    }

    function startDmodeFocus() {
        const planData = getSharedPlanTodayTasks();
        let targetTaskId = null;
        if (planData && Array.isArray(planData.todayItems) && planData.todayItems.length > 0) {
            const inProg = planData.todayItems.find(pt => pt.task && pt.task.isInProgress && !pt.task.completed);
            if (inProg) {
                targetTaskId = inProg.task.id;
            } else {
                const nextUnfinished = planData.todayItems.find(pt => pt.task && !pt.task.completed);
                if (nextUnfinished) {
                    targetTaskId = nextUnfinished.task.id;
                }
            }
        }

        if (targetTaskId && window.TempoFocusZone && typeof window.TempoFocusZone.open === 'function') {
            window.TempoFocusZone.open({ taskId: targetTaskId });
        } else if (window.TempoFocusZone && typeof window.TempoFocusZone.openQuickEntry === 'function') {
            window.TempoFocusZone.openQuickEntry();
        } else if (window.TempoTriage && typeof window.TempoTriage.launchFocusMode === 'function') {
            window.TempoTriage.launchFocusMode();
        }
    }

    function startDmodeTaskFocus(taskId) {
        if (window.TempoPlanWorkspace && typeof window.TempoPlanWorkspace.startTaskFocus === 'function') {
            window.TempoPlanWorkspace.startTaskFocus(taskId);
        } else if (window.TempoFocusZone && typeof window.TempoFocusZone.open === 'function') {
            window.TempoFocusZone.open({ taskId: taskId });
        }
    }

    function openPlanWorkspace() {
        if (window.TempoPlanWorkspace && typeof window.TempoPlanWorkspace.open === 'function') {
            window.TempoPlanWorkspace.open();
        } else if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
            window.TempoApp.navigateTo('plan-workspace');
        } else {
            window.location.hash = '#plan-workspace';
        }
    }

    function restoreDefaultHome() {
        applyModeVisibility(MODES.DEFAULT);
        renderDmodeHome();
    }

    function isCleanShortName(str) {
        if (!str || typeof str !== 'string') return false;
        const trimmed = str.trim();
        if (trimmed.length < 2 || trimmed.length > 14) return false;
        // Disqualify if it has digits, email symbols, or technical separators
        if (/[0-9@._+\-\\/#$!%^&*()=~`|[\]{}<>;:,"'?]/.test(trimmed)) return false;
        try {
            if (!/^[\p{L}]+$/u.test(trimmed)) return false;
        } catch (e) {
            if (!/^[a-zA-Z]+$/.test(trimmed)) return false;
        }
        return true;
    }

    function formatCapitalized(str) {
        if (!str) return '';
        const s = str.trim();
        return s.charAt(0).toUpperCase() + s.slice(1);
    }

    function getSafeGreetingInfo(profile) {
        if (!profile) {
            try {
                profile = JSON.parse(localStorage.getItem('tempo_user_profile') || localStorage.getItem('tempo_profile') || 'null');
            } catch(e) {}
        }
        const fallbackText = window.t ? window.t('modes.default.greetingFallback', {}, 'Hi there 👋') : 'Hi there 👋';
        if (!profile) {
            return { name: 'there', greetingText: fallbackText, isFallback: true };
        }

        const makeGreeting = (clean) => {
            return window.t ? window.t('modes.default.greeting', { name: clean }, `Hi, ${clean} 👋`) : `Hi, ${clean} 👋`;
        };

        // 0) Intelligent cultural greeting extraction (Vietnamese given name last vs Western given name first)
        if (window.TempoAuth && typeof window.TempoAuth.extractGreetingName === 'function') {
            const extracted = window.TempoAuth.extractGreetingName(profile.display_name || profile.full_name);
            if (extracted && isCleanShortName(extracted)) {
                const clean = formatCapitalized(extracted);
                return { name: clean, greetingText: makeGreeting(clean), isFallback: false };
            }
        }

        // 1) preferred_name / display_name
        const pref = profile.preferred_name || profile.display_name;
        if (pref && isCleanShortName(pref)) {
            const clean = formatCapitalized(pref);
            return { name: clean, greetingText: makeGreeting(clean), isFallback: false };
        }

        // 2) first_name
        const first = profile.first_name;
        if (first && isCleanShortName(first)) {
            const clean = formatCapitalized(first);
            return { name: clean, greetingText: makeGreeting(clean), isFallback: false };
        }

        // 3) clean short extracted from full_name
        const full = profile.full_name;
        if (full && typeof full === 'string') {
            const firstToken = full.trim().split(/\s+/)[0];
            if (firstToken && isCleanShortName(firstToken)) {
                const clean = formatCapitalized(firstToken);
                return { name: clean, greetingText: makeGreeting(clean), isFallback: false };
            }
        }

        // 4) Fallback
        return { name: 'there', greetingText: fallbackText, isFallback: true };
    }

    function renderEmodeHome() {
        applyModeVisibility(MODES.EMERGENCY);

        const emodeBox = document.getElementById('emode-home-content');
        if (!emodeBox) return;

        // Inspect shared emergency state: Prefer active plan from TempoPlanStore, fallback to TempoEmergencyFlow
        const activeStorePlan = window.TempoPlanStore && window.TempoPlanStore.getActivePlan
            ? window.TempoPlanStore.getActivePlan('emergency')
            : null;
        let confirmedPlan = (activeStorePlan && activeStorePlan.plannedTasks && activeStorePlan.plannedTasks.length > 0)
            ? activeStorePlan
            : ((window.TempoEmergencyFlow && window.TempoEmergencyFlow.getConfirmedPlan) ? window.TempoEmergencyFlow.getConfirmedPlan() : null);

        if (!confirmedPlan || !confirmedPlan.plannedTasks || confirmedPlan.plannedTasks.length === 0) {
            confirmedPlan = getUrmodeActivePlan();
        }

        const currentStage = window.TempoEmergencyFlow && window.TempoEmergencyFlow.getCurrentStage
            ? window.TempoEmergencyFlow.getCurrentStage()
            : 'entry';
        const availabilityDays = (confirmedPlan && confirmedPlan.availabilityDays && confirmedPlan.availabilityDays.length > 0)
            ? confirmedPlan.availabilityDays
            : ((window.TempoEmergencyFlow && window.TempoEmergencyFlow.getAvailabilityDays) ? window.TempoEmergencyFlow.getAvailabilityDays() : []);

        const todayStr = getTodayISOString();
        const profile = window.TempoAuth ? window.TempoAuth.getCurrentProfile() : null;
        const greetingInfo = getSafeGreetingInfo(profile);

        // -----------------------------------------------------------------
        // DETERMINE DYNAMIC HOME STATE
        // -----------------------------------------------------------------
        let activeHomeState = 'PLAN_INCOMPLETE'; // Default if setup unfinished

        if (!confirmedPlan || !confirmedPlan.plannedTasks || confirmedPlan.plannedTasks.length === 0) {
            activeHomeState = 'PLAN_INCOMPLETE';
        } else {
            // Collect all tasks across plannedTasks, unarrangedTasks, and tasks to evaluate overall completion
            const allPlanTasks = [];
            const seenTaskIds = new Set();
            if (Array.isArray(confirmedPlan.plannedTasks)) {
                confirmedPlan.plannedTasks.forEach(pt => {
                    if (pt && pt.task && pt.task.id && !seenTaskIds.has(String(pt.task.id))) {
                        seenTaskIds.add(String(pt.task.id));
                        allPlanTasks.push(pt.task);
                    }
                });
            }
            if (Array.isArray(confirmedPlan.unarrangedTasks)) {
                confirmedPlan.unarrangedTasks.forEach(u => {
                    const t = (u && u.task) ? u.task : u;
                    if (t && t.id && !seenTaskIds.has(String(t.id))) {
                        seenTaskIds.add(String(t.id));
                        allPlanTasks.push(t);
                    }
                });
            }
            if (Array.isArray(confirmedPlan.tasks)) {
                confirmedPlan.tasks.forEach(t => {
                    if (t && t.id && !seenTaskIds.has(String(t.id))) {
                        seenTaskIds.add(String(t.id));
                        allPlanTasks.push(t);
                    }
                });
            }

            const allCompleted = allPlanTasks.length > 0 && allPlanTasks.every(t => t.completed === true);

            if (allCompleted) {
                activeHomeState = 'PLAN_COMPLETE';
            } else {
                // Check for overdue planned tasks with passed deadlines
                const allPlanned = confirmedPlan.plannedTasks || [];
                const staleTasks = allPlanned.filter(pt => {
                    if (!pt.task || pt.task.completed === true || pt.task.isCompleted === true || pt.task.status === 'completed') return false;
                    return isTaskOverdue(pt.task, confirmedPlan);
                });

                if (staleTasks.length > 0 && !sessionFlags.dismissedStaleWarning) {
                    activeHomeState = 'PLAN_STALE';
                } else {
                    // Check for tasks with missed schedule (scheduled date passed, not overdue, not dismissed)
                    const missedScheduleTasks = allPlanned.filter(pt => {
                        const t = pt.task || pt;
                        if (!t || t.completed === true || t.isCompleted === true || t.status === 'completed') return false;
                        if (isTaskOverdue(t, confirmedPlan)) return false;
                        if (!isTaskMissedSchedule(pt, confirmedPlan)) return false;
                        return !isMissedSchedulePromptDismissed(t.id, pt.dayDate);
                    });

                    if (missedScheduleTasks.length > 0) {
                        activeHomeState = 'PLAN_MISSED_SCHEDULE';
                    } else {
                        // Check tasks planned for today
                        const todayTasks = allPlanned.filter(pt => pt.dayDate === todayStr);

                        if (todayTasks.length === 0) {
                            activeHomeState = 'NO_WORK_TODAY';
                        } else {
                            const todayCompleted = todayTasks.every(pt => pt.task && pt.task.completed === true);

                            if (todayCompleted) {
                                activeHomeState = 'TODAY_COMPLETE';
                            } else {
                                // Check if today's planned time has ended with incomplete work
                                const timeEnded = checkIsTodayPlannedTimeEnded(availabilityDays, todayStr);
                                if (timeEnded && !sessionFlags.dismissedTimeEndedToday) {
                                    activeHomeState = 'TIME_ENDED_WITH_INCOMPLETE_WORK';
                                } else {
                                    activeHomeState = 'ACTIVE_TODAY';
                                }
                            }
                        }
                    }
                }
            }
        }

        currentActiveHomeState = activeHomeState;

        // Render appropriate view according to state with stable ~65 / 35 outer shell
        emodeBox.innerHTML = `
            <div class="relative space-y-6 sm:space-y-8" data-tempo-ui="urgent-home-shell">
                ${renderEmodeHeader(greetingInfo)}
                <div class="urgent-home-main-grid">
                    <!-- LEFT COLUMN (~65%) -->
                    <div class="urgent-left-col space-y-5" data-tempo-ui="urgent-left-col">
                        ${renderEmodePrimarySection(activeHomeState, { confirmedPlan, currentStage, availabilityDays, todayStr, greetingInfo })}
                        ${renderSupportRowHTML()}
                    </div>
                    <!-- RIGHT COLUMN (~35%) -->
                    <div class="urgent-right-col space-y-5 bg-white/0" data-tempo-ui="urgent-plan-today">
                        ${renderEmodeRightCol(activeHomeState, { confirmedPlan, todayStr, currentStage })}
                    </div>
                </div>
                ${renderEmodeLowerSection()}
            </div>
            <div id="urmode-task-modal-root">
                ${renderUrmodeTaskDetailModalHTML()}
            </div>
        `;

        syncModeSelectorDOM(MODES.EMERGENCY);

        // Trigger community posts preview sync for urgent feed
        if (window.TempoCommunity && typeof window.TempoCommunity.renderUrgentPreview === 'function') {
            window.TempoCommunity.renderUrgentPreview();
        }

        // Check if Reset popup should appear over the Urmode dashboard
        if (window.TempoUrmodeFlow && typeof window.TempoUrmodeFlow.shouldShowReset === 'function' && window.TempoUrmodeFlow.shouldShowReset()) {
            window.TempoUrmodeFlow.consumeResetFlag();
            window.TempoUrmodeFlow.showResetPopup();
        }

        if (typeof syncUmodeCreateNotesAlignment === 'function') {
            requestAnimationFrame(syncUmodeCreateNotesAlignment);
        }
    }

    function resolveUserDisplayName(greetingInfo) {
        if (greetingInfo && !greetingInfo.isFallback && greetingInfo.name && greetingInfo.name !== 'there') {
            return greetingInfo.name;
        }
        const profile = window.TempoAuth && typeof window.TempoAuth.getCurrentProfile === 'function'
            ? window.TempoAuth.getCurrentProfile()
            : null;
        const user = window.TempoAuth && typeof window.TempoAuth.getCurrentUser === 'function'
            ? window.TempoAuth.getCurrentUser()
            : null;

        let localProfile = null;
        try {
            localProfile = JSON.parse(localStorage.getItem('tempo_user_profile') || localStorage.getItem('tempo_profile') || 'null');
        } catch(e) {}

        const raw = profile?.display_name || profile?.full_name || profile?.preferred_name || profile?.first_name
            || user?.user_metadata?.display_name || user?.user_metadata?.full_name
            || localProfile?.display_name || localProfile?.full_name || localProfile?.name;

        if (raw && typeof raw === 'string') {
            const trimmed = raw.trim();
            if (trimmed && trimmed.toLowerCase() !== 'undefined' && trimmed.toLowerCase() !== 'null' && trimmed.toLowerCase() !== 'there') {
                return typeof formatCapitalized === 'function' ? formatCapitalized(trimmed) : trimmed;
            }
        }
        return null;
    }

    function renderEmodeHeader(greetingInfo) {
        const displayName = resolveUserDisplayName(greetingInfo);
        const isVi = typeof isViLocale === 'function' ? isViLocale() : (window.TempoI18n?.getCurrentLanguage?.() === 'vi');
        const greetingHeading = displayName
            ? (window.t ? window.t('modes.urgent.welcomeHeading', { name: escapeHTML(displayName) }, (isVi ? `Chào ${escapeHTML(displayName)}, cùng bắt đầu nhé?` : `Hi, ${escapeHTML(displayName)}, ready to get things done?`)) : (isVi ? `Chào ${escapeHTML(displayName)}, cùng bắt đầu nhé?` : `Hi, ${escapeHTML(displayName)}, ready to get things done?`))
            : (window.t ? window.t('modes.urgent.welcomeHeadingFallback', {}, (isVi ? 'Chào bạn, cùng bắt đầu nhé?' : 'Hi, ready to get things done?')) : (isVi ? 'Chào bạn, cùng bắt đầu nhé?' : 'Hi, ready to get things done?'));

        return `
            <div class="relative pb-1 space-y-2">
                <!-- Top Mode Selector Row -->
                <div class="flex items-center justify-between gap-4">
                    <!-- Anchored Mode Selector Dropdown -->
                    <div id="home-mode-selector-wrapper" class="relative inline-block text-left">
                        <button id="btn-home-mode-selector" 
                                type="button" 
                                data-tempo-ui="mode-selector-btn"
                                onclick="window.TempoMode.toggleModeDropdown(event)" 
                                class="h-8 px-3.5 rounded-full text-xs font-bold bg-[#FBF0E9] text-[#D79277] hover:bg-[#F2DCD0] border border-[#D79277]/50 transition flex items-center space-x-1.5 shadow-2xs cursor-pointer focus:outline-none focus:ring-2 focus:ring-[#D79277]/40"
                                aria-haspopup="true"
                                aria-expanded="false"
                                title="Switch Tempo Mode">
                            <span class="text-xs text-[#D79277] leading-none select-none">⚡</span>
                            <span class="font-extrabold tracking-tight">${window.t ? window.t('modes.urgent.name', {}, 'Urgent Mode') : 'Urgent Mode'}</span>
                            <span class="text-[10px] ml-0.5 text-[#D79277]/80 leading-none select-none">▾</span>
                        </button>
                        <div id="home-mode-selector-dropdown" class="hidden absolute left-0 mt-2 w-72 sm:w-80 bg-white rounded-2xl shadow-xl border border-[#EAE4DF] z-50 overflow-hidden" role="menu"></div>
                    </div>
                </div>

                <!-- Page Subheader Greeting -->
                <div class="text-2xl sm:text-[28px] font-extrabold text-[#484541] tracking-tight flex items-center gap-2.5 pt-1">
                    <span>👋</span>
                    <span>${greetingHeading}</span>
                </div>
            </div>
        `;
    }

    function renderEmodePrimarySection(state, ctx) {
        const { confirmedPlan, currentStage, availabilityDays, todayStr, greetingInfo } = ctx;

        switch (state) {
            case 'PLAN_INCOMPLETE':
                return renderStatePlanIncomplete(currentStage, greetingInfo);

            case 'PLAN_COMPLETE':
                return renderStatePlanComplete(confirmedPlan, greetingInfo);

            case 'PLAN_STALE':
                return renderStatePlanStale(confirmedPlan, todayStr, greetingInfo);

            case 'PLAN_MISSED_SCHEDULE':
                return renderStatePlanMissedSchedule(confirmedPlan, todayStr, greetingInfo);

            case 'TIME_ENDED_WITH_INCOMPLETE_WORK':
                return renderStateTimeEnded(confirmedPlan, todayStr, greetingInfo);

            case 'TODAY_COMPLETE':
                return renderStateTodayComplete(confirmedPlan, todayStr, greetingInfo);

            case 'NO_WORK_TODAY':
                return renderStateNoWorkToday(confirmedPlan, todayStr, greetingInfo);

            case 'ACTIVE_TODAY':
            default:
                return renderStateActiveToday(confirmedPlan, todayStr, greetingInfo);
        }
    }

    const renderStateBody = renderEmodePrimarySection;

    // -------------------------------------------------------------------------
    // STATE A: PLAN_INCOMPLETE
    // -------------------------------------------------------------------------
    function renderStatePlanIncomplete(currentStage, greetingInfo) {
        const stageNames = {
            'entry': 'Settle / Reset Checkpoint',
            'reality-check': 'Reality Check (Task Dump)',
            'prioritize': 'Prioritize + Estimate Assessment',
            'priority-review': 'Priority Review & Buckets',
            'available-time': 'Available Time Entry',
            'feasibility': 'Feasibility & Workload Check',
            'generating': 'Generating Plan',
            'plan-review': 'Urgent Plan Review & Schedule',
            'handoff': 'Start Working Handoff'
        };

        const isEntryStage = !currentStage || currentStage === 'entry';
        const currentStageTitle = stageNames[currentStage] || 'Urgent Setup';

        return `
            <div class="urgent-card-now from-[#FFF9F5] border-[#FFD2BA] rounded-3xl p-6 sm:p-7 soft-card-shadow relative overflow-hidden transition flex flex-col justify-between" style="background-color: #faeddb; border: 1px solid #000000; min-height: 290px;" data-tempo-ui="urgent-task-now">
                <div class="relative z-10 space-y-3">
                    <!-- Badge Row: YOUR WORKING PLAN (with sr-only YOUR URGENT PLAN) -->
                    <div class="flex items-center justify-between mb-3.5">
                        <div class="flex items-center space-x-2">
                            <span class="w-2.5 h-2.5 rounded-full bg-[#D79277] inline-block"></span>
                            <span class="px-4 py-1.5 rounded-full text-xs font-bold bg-[#D79277] text-white shadow-2xs">
                                ${window.t ? window.t('modes.urgent.yourWorkingPlanUpper', {}, 'YOUR WORKING PLAN') : 'YOUR WORKING PLAN'}
                            </span>
                            <span class="text-[11px] font-extrabold uppercase tracking-wider text-[#B83D08] sr-only">
                                ${window.t ? window.t('modes.urgent.yourUrgentPlanUpper', {}, 'YOUR URGENT PLAN') : 'YOUR URGENT PLAN'}
                            </span>
                        </div>
                    </div>

                    <div class="text-xs sm:text-sm font-semibold text-[#6F6B68] sr-only">
                        ${escapeHTML(greetingInfo ? greetingInfo.greetingText : 'Hi there 👋')}
                    </div>

                    <!-- Title Block -->
                    <div class="space-y-1">
                        <h3 class="font-heading text-2xl sm:text-[34px] font-extrabold text-[#484541] tracking-tight leading-snug">
                            ${isEntryStage
                                ? (window.t ? window.t('modes.urgent.notSetUpYet', {}, "Bạn chưa thiết lập kế hoạch làm việc") : "Bạn chưa thiết lập kế hoạch làm việc")
                                : (window.t ? window.t('modes.urgent.statePlanIncomplete', {}, "Bạn vẫn đang thiết lập kế hoạch.") : "Bạn vẫn đang thiết lập kế hoạch.")
                            }
                        </h3>
                        <span class="sr-only">Bạn vẫn đang thiết lập kế hoạch.</span>
                    </div>

                    <!-- Subtask / Step Row -->
                    <div class="flex items-center space-x-2.5 my-3">
                        <div class="w-4 h-4 rounded border-2 border-[#8C6C63]/60 bg-transparent flex items-center justify-center shrink-0"></div>
                        <p class="italic text-sm sm:text-base font-medium text-[#5D5954]">
                            ${isEntryStage
                                ? (window.t ? window.t('modes.urgent.notSetUpYetDesc', {}, 'Set up your working plan to organize your day, or execute an urgent task immediately.') : 'Set up your working plan to organize your day, or execute an urgent task immediately.')
                                : `${window.t ? window.t('modes.urgent.statePlanIncompleteDesc', {}, 'Your urgent plan setup is in progress at step:') : 'Your urgent plan setup is in progress at step:'} <strong class="font-semibold text-[#484541]">${escapeHTML(currentStageTitle)}</strong>.`
                            }
                        </p>
                    </div>
                </div>

                <!-- Action Buttons Row -->
                <div class="relative z-10 pt-4 border-t border-[#E8D9C5] flex flex-wrap items-center gap-3">
                    ${isEntryStage ? `
                        <button onclick="if (window.TempoUrmodeFlow && window.TempoUrmodeFlow.startSetupFlow) { window.TempoUrmodeFlow.startSetupFlow(); } else { window.TempoApp.navigateTo('emergency'); window.TempoEmergencyFlow.goToStage('reality-check'); }"
                                class="btn-primary btn-terracotta px-5 py-2.5 rounded-2xl font-bold text-xs sm:text-sm shadow-sm inline-flex items-center space-x-2 transition cursor-pointer">
                            <span>Setup my plan</span>
                            <span>→</span>
                        </button>
                        <button onclick="if (window.TempoUrmodeFlow && window.TempoUrmodeFlow.openQuickTaskModal) { window.TempoUrmodeFlow.openQuickTaskModal(); }"
                                class="px-5 py-2.5 rounded-2xl font-bold text-xs sm:text-sm bg-white hover:bg-[#FAF7F4] text-[#B83D08] border border-[#FFD2BA] shadow-2xs inline-flex items-center space-x-1.5 transition cursor-pointer">
                            <span>⚡</span>
                            <span>Execute my task now</span>
                        </button>
                    ` : `
                        <button onclick="window.TempoApp.navigateTo('emergency'); window.TempoEmergencyFlow.goToStage('${currentStage}');"
                                class="btn-primary btn-terracotta px-5 py-2.5 rounded-2xl font-bold text-xs sm:text-sm shadow-sm inline-flex items-center space-x-2 transition cursor-pointer">
                            <span>${window.t ? window.t('modes.urgent.continueBuilding', {}, 'Continue building my plan') : 'Continue building my plan'}</span>
                            <span>→</span>
                        </button>
                        <button onclick="if (window.TempoUrmodeFlow && window.TempoUrmodeFlow.openQuickTaskModal) { window.TempoUrmodeFlow.openQuickTaskModal(); }"
                                class="px-5 py-2.5 rounded-2xl font-bold text-xs sm:text-sm bg-white hover:bg-[#FAF7F4] text-[#B83D08] border border-[#FFD2BA] shadow-2xs inline-flex items-center space-x-1.5 transition cursor-pointer">
                            <span>⚡</span>
                            <span>Execute my task now</span>
                        </button>
                    `}
                    <button onclick="window.TempoMode.openChangeModeModal()" 
                            class="px-5 py-2.5 rounded-2xl font-bold text-xs sm:text-sm bg-white hover:bg-[#FAF7F4] text-[#6F6B68] border border-[#EAE4DF] shadow-2xs inline-flex items-center transition cursor-pointer">
                        ${window.t ? window.t('modes.selector.switchMode', {}, 'Switch mode') : 'Switch mode'}
                    </button>
                </div>
            </div>
        `;
    }

    // -------------------------------------------------------------------------
    // STATE G: PLAN_COMPLETE
    // -------------------------------------------------------------------------
    function renderStatePlanComplete(confirmedPlan, greetingInfo) {
        return `
            <div class="urgent-card-now from-[#FFF9F5] border-[#FFD2BA] rounded-3xl p-6 sm:p-7 soft-card-shadow relative overflow-hidden transition flex flex-col justify-between" style="background-color: #faeddb; border: 1px solid #000000; min-height: 290px;" data-tempo-ui="urgent-task-now">
                <div class="relative z-10 space-y-3">
                    <!-- Badge Row: ACUTE CRISIS CLEARED -->
                    <div class="flex items-center justify-between mb-3.5">
                        <div class="flex items-center space-x-2">
                            <span class="w-2.5 h-2.5 rounded-full bg-emerald-600 inline-block"></span>
                            <span class="px-4 py-1.5 rounded-full text-xs font-bold bg-emerald-700 text-white shadow-2xs">
                                ${window.t ? window.t('modes.urgent.completed', {}, 'ACUTE CRISIS CLEARED') : 'ACUTE CRISIS CLEARED'}
                            </span>
                            <span class="text-[11px] font-extrabold uppercase tracking-widest text-[#166545] sr-only">
                                ${window.t ? window.t('modes.urgent.completed', {}, 'ACUTE CRISIS CLEARED') : 'ACUTE CRISIS CLEARED'}
                            </span>
                            <span class="sr-only">Your Urgent Plan is complete. Stay in Urgent Mode</span>
                        </div>
                    </div>

                    <div class="text-xs sm:text-sm font-semibold text-[#6F6B68] sr-only">
                        ${escapeHTML(greetingInfo ? greetingInfo.greetingText : 'Hi there 👋')}
                    </div>

                    <!-- Title Block -->
                    <div class="space-y-1">
                        <h3 class="font-heading text-2xl sm:text-[34px] font-extrabold text-[#484541] tracking-tight leading-snug">
                            You did it! 🎉
                        </h3>
                    </div>

                    <!-- Status Row / Message -->
                    <div class="flex items-center space-x-2.5 my-2">
                        <div class="w-4 h-4 rounded border-2 border-emerald-600/60 bg-emerald-100 flex items-center justify-center shrink-0 text-emerald-700 text-[10px] font-bold">✓</div>
                        <p class="italic text-sm sm:text-base font-medium text-[#5D5954]">
                            You've completed everything in your Working Plan. Would you like to switch to Recovery Mode and take a breather?
                        </p>
                    </div>

                    <!-- Mode Recommendation Suggestion -->
                    <div class="p-3 bg-white/90 border border-[#FFD2BA] rounded-2xl max-w-xl text-left flex items-start space-x-3 text-xs text-[#166545] my-1">
                        <span class="text-base">🌱</span>
                        <div class="space-y-0.5">
                            <p class="font-bold">Tempo Recommendation:</p>
                            <p class="text-[#202124] leading-relaxed">Your workload has eased up. Shifting toward <strong>${window.t ? window.t('modes.recovery.name', {}, 'Recovery Mode') : 'Recovery Mode'}</strong> can help you restore energy and rebuild a sustainable pace.</p>
                        </div>
                    </div>
                </div>

                <!-- Action Buttons Row -->
                <div class="relative z-10 pt-4 border-t border-[#E8D9C5] flex flex-wrap items-center gap-2.5">
                    <button onclick="window.TempoMode.setMode('recovery')" 
                            class="btn-primary btn-terracotta px-5 py-2.5 rounded-2xl font-bold text-xs sm:text-sm shadow-sm inline-flex items-center transition cursor-pointer">
                        <span class="sr-only">Shift to Recovery Mode - </span><span>Yes, let's recharge →</span>
                    </button>
                    <button onclick="if (window.TempoMode && typeof window.TempoMode.openUcheck === 'function') { window.TempoMode.openUcheck({ sourceContext: 'emergency' }); } else { window.TempoMode.setMode('unclear'); }" 
                            class="px-5 py-2.5 rounded-2xl font-bold text-xs sm:text-sm bg-white hover:bg-[#FAF7F4] text-[#6F6B68] border border-[#EAE4DF] shadow-2xs inline-flex items-center transition cursor-pointer">
                        Not sure yet
                    </button>
                    <button onclick="window.TempoApp.navigateTo('plan-workspace')" 
                            class="px-5 py-2.5 rounded-2xl font-bold text-xs sm:text-sm bg-white hover:bg-[#FAF7F4] text-[#6F6B68] border border-[#EAE4DF] shadow-2xs inline-flex items-center transition cursor-pointer">
                        Update my plan
                    </button>
                </div>
            </div>
        `;
    }

    // -------------------------------------------------------------------------
    // STATE F: PLAN_STALE
    // -------------------------------------------------------------------------
    function renderStatePlanStale(confirmedPlan, todayStr, greetingInfo) {
        const staleTasks = (confirmedPlan?.plannedTasks || []).filter(pt => {
            if (!pt.task || pt.task.completed === true || pt.task.isCompleted === true || pt.task.status === 'completed') return false;
            return isTaskOverdue(pt.task, confirmedPlan);
        });

        const currentOverdue = staleTasks[0];
        const overdueTask = currentOverdue?.task;
        const taskName = overdueTask?.name || 'Overdue Task';
        const isVi = typeof isViLocale === 'function' ? isViLocale() : false;

        const taskOverdueHeading = (window.t ? window.t('modes.urgent.taskOverdue') : null) || (isVi ? 'TASK TRỄ DEADLINE' : 'TASK OVERDUE');
        const thisTaskIsOverdue = (window.t ? window.t('modes.urgent.thisTaskIsOverdue') : null) || (isVi ? 'Task này đã trễ Deadline' : 'This task is overdue');
        const taskOverdueDesc = (window.t ? window.t('modes.urgent.taskOverdueDesc') : null) || (isVi ? 'Task này đã trễ deadline. Bạn muốn xóa, đánh dấu hoàn thành hay cập nhật lại?' : 'Looks like this task has passed its due date. Would you like to clear it, mark it as done, or update it?');
        const overdueBadgeText = (window.t ? window.t('modes.urgent.overdueBadge') : null) || (isVi ? 'TRỄ DEADLINE' : 'OVERDUE');
        const scheduledLabelText = (window.t ? window.t('modes.urgent.scheduledLabel') : null) || (isVi ? 'Ngày lên lịch:' : 'Scheduled:');
        const deadlineLabelText = (window.t ? window.t('modes.urgent.deadlineLabel') : null) || 'Deadline:';
        const clearThisTaskText = (window.t ? window.t('modes.urgent.clearThisTask') : null) || (isVi ? 'Xóa task này' : 'Clear this task');
        const markAsDoneText = (window.t ? window.t('modes.urgent.markAsDone') : null) || (isVi ? 'Hoàn thành' : 'Mark as done');
        const editTaskText = (window.t ? window.t('modes.urgent.editTask') : null) || (isVi ? 'Chỉnh sửa task' : 'Edit task');

        return `
            <div class="urgent-card-now from-[#FFF9F5] border-[#FFD2BA] rounded-3xl p-6 sm:p-7 soft-card-shadow relative overflow-hidden transition flex flex-col justify-between" style="background-color: #faeddb; border: 1px solid #000000; min-height: 290px;" data-tempo-ui="urgent-task-now">
                <div class="relative z-10 space-y-3">
                    <!-- Badge Row: OVERDUE TASK -->
                    <div class="flex items-center justify-between mb-3.5">
                        <div class="flex items-center space-x-2">
                            <span class="w-2.5 h-2.5 rounded-full bg-amber-600 inline-block"></span>
                            <span class="px-4 py-1.5 rounded-full text-xs font-bold bg-amber-600 text-white shadow-2xs">
                                ${taskOverdueHeading}
                            </span>
                            <span class="text-[11px] font-bold uppercase tracking-wider text-[#B83D08] sr-only">SCHEDULE UPDATE NEEDED</span>
                            <span class="sr-only">Your plan needs an update.</span>
                        </div>
                    </div>

                    <div class="text-xs sm:text-sm font-semibold text-[#6F6B68] sr-only">
                        ${escapeHTML(greetingInfo ? greetingInfo.greetingText : 'Hi there 👋')}
                    </div>

                    <!-- Title Block -->
                    <div class="space-y-1">
                        <h3 class="font-heading text-2xl sm:text-[34px] font-extrabold text-[#484541] tracking-tight leading-snug">
                            ${thisTaskIsOverdue}
                        </h3>
                    </div>

                    <!-- Status Description / Message -->
                    <div class="flex items-center space-x-2.5 my-2">
                        <div class="w-4 h-4 rounded border-2 border-amber-600/60 bg-transparent flex items-center justify-center shrink-0 text-amber-700 text-[10px] font-bold">!</div>
                        <p class="italic text-sm sm:text-base font-medium text-[#5D5954]">
                            ${taskOverdueDesc}
                        </p>
                    </div>

                    <!-- Overdue Task Info Box -->
                    <div class="p-3.5 bg-white/90 rounded-2xl border border-[#FFD2BA] text-xs text-amber-950 space-y-1.5 my-1">
                        <div class="flex items-center justify-between">
                            <span class="font-bold text-stone-800 text-sm sm:text-base">• ${escapeHTML(taskName)}</span>
                            <span class="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase tracking-wider bg-amber-100 text-amber-800 border border-amber-300">${overdueBadgeText}</span>
                        </div>
                        <div class="text-stone-500 text-[11px] flex flex-wrap items-center gap-2">
                            ${currentOverdue?.dayDate ? `<span>${scheduledLabelText} ${escapeHTML(formatScheduledDateLabel(currentOverdue.dayDate, isVi ? 'vi' : 'en'))}</span>` : ''}
                            ${overdueTask?.hasDeadline && overdueTask?.deadlineDate ? `<span>• ${deadlineLabelText} ${window.TempoI18n ? window.TempoI18n.formatDeadline(overdueTask.deadlineDate, overdueTask.deadlineTime) : formatHumanDeadline(overdueTask.deadlineDate, overdueTask.deadlineTime)}</span>` : ''}
                            ${overdueTask?.durationLabel ? `<span>• ~${escapeHTML(overdueTask.durationLabel)}</span>` : ''}
                        </div>
                    </div>
                </div>

                <!-- Action Buttons Row (Clear task, Mark as done, Edit task) -->
                <div class="relative z-10 pt-4 border-t border-[#E8D9C5] flex flex-wrap items-center gap-3">
                    <button type="button" onclick="window.TempoMode.promptClearOverdueTask('${overdueTask?.id}')"
                            class="px-5 py-2.5 rounded-2xl font-bold text-xs sm:text-sm bg-white hover:bg-rose-50 text-rose-700 border border-rose-200 shadow-2xs inline-flex items-center transition cursor-pointer">
                        ${clearThisTaskText}
                    </button>
                    <button type="button" onclick="window.TempoMode.markOverdueTaskDone('${overdueTask?.id}')"
                            class="btn-primary btn-terracotta bg-emerald-600 px-5 py-2.5 rounded-2xl font-bold text-xs sm:text-sm shadow-sm inline-flex items-center transition cursor-pointer">
                        <span class="sr-only">Mark this task as finished - </span><span>${markAsDoneText}</span>
                    </button>
                    <button type="button" onclick="window.TempoApp.navigateTo('plan-workspace'); if (window.TempoPlanWorkspace && window.TempoPlanWorkspace.selectTask) { window.TempoPlanWorkspace.selectTask('${overdueTask?.id}'); }"
                            class="px-5 py-2.5 rounded-2xl font-bold text-xs sm:text-sm bg-white hover:bg-[#FAF7F4] text-[#6F6B68] border border-[#EAE4DF] shadow-2xs inline-flex items-center transition cursor-pointer">
                        <span class="sr-only">Update my plan - </span><span>${editTaskText}</span>
                    </button>
                </div>
            </div>
        `;
    }

    // -------------------------------------------------------------------------
    // STATE G: PLAN_MISSED_SCHEDULE
    // -------------------------------------------------------------------------
    function renderStatePlanMissedSchedule(confirmedPlan, todayStr, greetingInfo) {
        const missedTasks = (confirmedPlan?.plannedTasks || []).filter(pt => {
            const t = pt.task || pt;
            if (!t || t.completed === true || t.isCompleted === true || t.status === 'completed') return false;
            if (isTaskOverdue(t, confirmedPlan)) return false;
            if (!isTaskMissedSchedule(pt, confirmedPlan)) return false;
            return !isMissedSchedulePromptDismissed(t.id, pt.dayDate);
        });

        const currentMissed = missedTasks[0];
        const missedTask = currentMissed?.task;
        const taskName = missedTask?.name || 'Scheduled Task';
        const isVi = isViLocale();

        const schedLabel = currentMissed?.dayDate ? formatScheduledDateLabel(currentMissed.dayDate, isVi) : (isVi ? 'ngày trước đó' : 'a past date');

        const schedDateFormatted = window.TempoI18n && typeof window.TempoI18n.formatCalendarDate === 'function'
            ? window.TempoI18n.formatCalendarDate(currentMissed?.dayDate, isVi ? 'vi' : 'en')
            : (currentMissed?.dayDate || '');

        let deadlineClause = '';
        if (missedTask?.hasDeadline && missedTask?.deadlineDate) {
            const dueDateFormatted = window.TempoI18n && typeof window.TempoI18n.formatCalendarDate === 'function'
                ? window.TempoI18n.formatCalendarDate(missedTask.deadlineDate, isVi ? 'vi' : 'en')
                : missedTask.deadlineDate;
            deadlineClause = isVi ? ` Deadline vẫn là ngày ${dueDateFormatted}.` : ` Your deadline is still ${dueDateFormatted}.`;
        }

        const description = isVi
            ? `Task này đã được sắp xếp vào ngày ${schedDateFormatted} nhưng chưa được hoàn thành.${deadlineClause} Bạn có muốn xếp lại lịch không?`
            : `This task was scheduled for ${schedDateFormatted}, but it hasn't been completed yet.${deadlineClause} Would you like to reschedule it?`;

        return `
            <div class="urgent-card-now from-[#FFF9F5] border-[#DCD5CF] rounded-3xl p-6 sm:p-7 soft-card-shadow relative overflow-hidden transition flex flex-col justify-between" style="background-color: #fbf9f6; border: 1px solid #c9c2bc; min-height: 290px;" data-tempo-ui="missed-schedule-prompt">
                <div class="relative z-10 space-y-3">
                    <!-- Badge Row: MISSED SCHEDULE -->
                    <div class="flex items-center justify-between mb-3.5">
                        <div class="flex items-center space-x-2">
                            <span class="w-2.5 h-2.5 rounded-full bg-[#7A6D65] inline-block"></span>
                            <span class="px-4 py-1.5 rounded-full text-xs font-bold bg-[#7A6D65] text-white shadow-2xs">
                                ${isVi ? 'TASK QUÁ LỊCH' : 'MISSED SCHEDULE'}
                            </span>
                        </div>
                    </div>

                    <div class="text-xs sm:text-sm font-semibold text-[#6F6B68] sr-only">
                        ${escapeHTML(greetingInfo ? greetingInfo.greetingText : 'Hi there 👋')}
                    </div>

                    <!-- Title Block -->
                    <div class="space-y-1">
                        <h3 class="font-heading text-2xl sm:text-[32px] font-extrabold text-[#484541] tracking-tight leading-snug">
                            ${isVi ? 'Task này đã bị quá lịch' : 'You missed this scheduled task'}
                        </h3>
                    </div>

                    <!-- Status Description / Message -->
                    <div class="flex items-center space-x-2.5 my-2">
                        <div class="w-4 h-4 rounded border-2 border-[#7A6D65]/60 bg-transparent flex items-center justify-center shrink-0 text-[#7A6D65] text-[10px] font-bold">⏱</div>
                        <p class="text-sm sm:text-base font-medium text-[#5D5954]">
                            ${escapeHTML(description)}
                        </p>
                    </div>

                    <!-- Task Info Box -->
                    <div class="p-3.5 bg-white/90 rounded-2xl border border-[#EAE4DF] text-xs text-stone-900 space-y-1.5 my-1">
                        <div class="flex items-center justify-between">
                            <span class="font-bold text-stone-800 text-sm sm:text-base">• ${escapeHTML(taskName)}</span>
                            <span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-stone-100 text-stone-700 border border-stone-300">
                                ${isVi ? 'TASK QUÁ LỊCH' : 'MISSED SCHEDULE'}
                            </span>
                        </div>
                        <div class="text-stone-500 text-[11px] flex flex-wrap items-center gap-2">
                            ${currentMissed?.dayDate ? `<span>${isVi ? 'Đã lên lịch:' : 'Was scheduled:'} ${escapeHTML(schedLabel)}</span>` : ''}
                            ${missedTask?.hasDeadline && missedTask?.deadlineDate ? `<span>• Deadline: ${window.TempoI18n ? window.TempoI18n.formatDeadline(missedTask.deadlineDate, missedTask.deadlineTime) : formatHumanDeadline(missedTask.deadlineDate, missedTask.deadlineTime)}</span>` : ''}
                            ${missedTask?.durationLabel ? `<span>• ~${escapeHTML(missedTask.durationLabel)}</span>` : ''}
                        </div>
                    </div>
                </div>

                <!-- Action Buttons Row (Reschedule task, Keep current schedule, Mark as done) -->
                <div class="relative z-10 pt-4 border-t border-[#EAE4DF] flex flex-wrap items-center gap-3">
                    <button type="button" onclick="window.TempoMode.rescheduleMissedTask('${missedTask?.id}')"
                            class="btn-primary btn-terracotta px-5 py-2.5 rounded-2xl font-bold text-xs sm:text-sm shadow-sm inline-flex items-center transition cursor-pointer">
                        <span>${isVi ? 'Xếp lại lịch' : 'Reschedule task'}</span>
                    </button>
                    <button type="button" onclick="window.TempoMode.keepCurrentSchedule('${missedTask?.id}')"
                            class="px-5 py-2.5 rounded-2xl font-bold text-xs sm:text-sm bg-white hover:bg-stone-50 text-stone-700 border border-stone-300 shadow-2xs inline-flex items-center transition cursor-pointer">
                        <span>${isVi ? 'Giữ lịch hiện tại' : 'Keep current schedule'}</span>
                    </button>
                    <button type="button" onclick="window.TempoMode.markMissedTaskDone('${missedTask?.id}')"
                            class="px-5 py-2.5 rounded-2xl font-bold text-xs sm:text-sm bg-white hover:bg-emerald-50 text-emerald-700 border border-emerald-200 shadow-2xs inline-flex items-center transition cursor-pointer">
                        <span>${isVi ? 'Đánh dấu hoàn thành' : 'Mark as done'}</span>
                    </button>
                </div>
            </div>
        `;
    }

    function rescheduleMissedTask(taskId) {
        if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
            window.TempoApp.navigateTo('plan-workspace');
        } else {
            window.location.hash = '#plan-workspace';
        }
        setTimeout(() => {
            if (window.TempoPlanWorkspace && typeof window.TempoPlanWorkspace.openRescheduleModal === 'function') {
                window.TempoPlanWorkspace.openRescheduleModal(taskId);
            }
        }, 100);
    }

    function keepCurrentSchedule(taskId) {
        let schedDate = '';
        const storePlan = window.TempoPlanStore && window.TempoPlanStore.getActivePlan ? window.TempoPlanStore.getActivePlan('emergency') : null;
        const pt = (storePlan?.plannedTasks || []).find(p => (p.task?.id === taskId || p.id === taskId));
        if (pt && pt.dayDate) schedDate = pt.dayDate;
        dismissMissedSchedulePrompt(taskId, schedDate);
        renderActiveModeHome();
    }

    function markMissedTaskDone(taskId) {
        clearMissedScheduleDismissal(taskId);
        if (typeof toggleTaskCompletion === 'function') {
            toggleTaskCompletion(taskId);
        } else if (window.TempoPlanWorkspace && typeof window.TempoPlanWorkspace.toggleTaskComplete === 'function') {
            window.TempoPlanWorkspace.toggleTaskComplete(taskId);
        }
        renderActiveModeHome();
    }

    // -------------------------------------------------------------------------
    // STATE E: TIME_ENDED_WITH_INCOMPLETE_WORK
    // -------------------------------------------------------------------------
    function renderStateTimeEnded(confirmedPlan, todayStr, greetingInfo) {
        const todayTasks = (confirmedPlan?.plannedTasks || []).filter(pt => pt.dayDate === todayStr);
        const topUnfinished = todayTasks.find(pt => !pt.task.completed) || todayTasks[0];
        const taskName = topUnfinished?.task?.name || 'Your planned work';

        // Check if stopping causes deadline conflict
        const hasDeadlineRisk = topUnfinished?.task?.hasDeadline && (
            topUnfinished.task.deadlineDate === todayStr ||
            topUnfinished.task.deadlineDate < todayStr
        );

        return `
            <div class="urgent-card-now from-[#FFF9F5] border-[#FFD2BA] rounded-3xl p-6 sm:p-7 soft-card-shadow relative overflow-hidden transition flex flex-col justify-between" style="background-color: #faeddb; border: 1px solid #000000; min-height: 290px;" data-tempo-ui="urgent-task-now">
                <div class="relative z-10 space-y-3">
                    <!-- Badge Row: PLANNED WINDOW ENDED -->
                    <div class="flex items-center justify-between mb-3.5">
                        <div class="flex items-center space-x-2">
                            <span class="w-2.5 h-2.5 rounded-full bg-[#D79277] inline-block"></span>
                            <span class="px-4 py-1.5 rounded-full text-xs font-bold bg-[#D79277] text-white shadow-2xs">
                                PLANNED WINDOW ENDED
                            </span>
                            <span class="text-[11px] font-bold uppercase tracking-wider text-[#B83D08] sr-only">PLANNED WINDOW ENDED</span>
                        </div>
                    </div>

                    <div class="text-xs sm:text-sm font-semibold text-[#6F6B68] sr-only">
                        ${escapeHTML(greetingInfo ? greetingInfo.greetingText : 'Hi there 👋')}
                    </div>

                    <!-- Title Block -->
                    <div class="space-y-1">
                        <h3 class="font-heading text-2xl sm:text-[34px] font-extrabold text-[#484541] tracking-tight leading-snug">
                            ${window.t ? window.t('modes.urgent.stateTimeEnded', {}, 'Your planned work time for today has ended.') : 'Your planned work time for today has ended.'}
                        </h3>
                    </div>

                    <!-- Subtask / In-Progress Row -->
                    <div class="flex items-center space-x-2.5 my-3">
                        <div class="w-4 h-4 rounded border-2 border-[#8C6C63]/60 bg-transparent flex items-center justify-center shrink-0"></div>
                        <p class="italic text-sm sm:text-base font-medium text-[#5D5954]">
                            <strong class="font-semibold text-[#484541]">${escapeHTML(taskName)}</strong> is still in progress.
                        </p>
                    </div>

                    ${hasDeadlineRisk ? `
                        <div class="p-3 bg-rose-50 border border-rose-200 rounded-2xl text-xs text-rose-900 space-y-1 my-2">
                            <div class="font-bold flex items-center space-x-1">
                                <span>⚠️</span>
                                <span>Upcoming Deadline Notice:</span>
                            </div>
                            <p>This task is due tonight or early tomorrow. If you choose to stop now, you may want to open your plan and allocate a morning block tomorrow.</p>
                        </div>
                    ` : ''}
                </div>

                <!-- Action Buttons Row -->
                <div class="relative z-10 pt-4 border-t border-[#E8D9C5] flex flex-wrap items-center gap-3">
                    <button onclick="window.TempoMode.keepWorkingToday()" 
                            class="btn-primary btn-terracotta px-5 py-2.5 rounded-2xl font-bold text-xs sm:text-sm shadow-sm inline-flex items-center space-x-2 transition cursor-pointer">
                        <span class="text-xs">▶</span>
                        <span>Keep working</span>
                    </button>
                    <button onclick="window.TempoMode.stopForToday()" 
                            class="px-5 py-2.5 rounded-2xl font-bold text-xs sm:text-sm bg-white hover:bg-[#FAF7F4] text-[#6F6B68] border border-[#EAE4DF] shadow-2xs inline-flex items-center transition cursor-pointer">
                        Stop for today
                    </button>
                    <button onclick="window.TempoApp.navigateTo('plan-workspace');" 
                            class="px-5 py-2.5 rounded-2xl font-bold text-xs sm:text-sm bg-white hover:bg-[#FAF7F4] text-[#6F6B68] border border-[#EAE4DF] shadow-2xs inline-flex items-center transition cursor-pointer">
                        Adjust my plan
                    </button>
                </div>
            </div>
        `;
    }

    // -------------------------------------------------------------------------
    // STATE C: TODAY_COMPLETE
    // -------------------------------------------------------------------------
    function renderStateTodayComplete(confirmedPlan, todayStr, greetingInfo) {
        // Find next planned date with tasks
        const futureTasks = (confirmedPlan?.plannedTasks || []).filter(pt => {
            return pt.dayDate > todayStr && (!pt.task || !pt.task.completed);
        });

        const isVi = typeof isViLocale === 'function' ? isViLocale() : false;
        const todaysWorkDoneText = (window.t ? window.t('modes.urgent.todaysWorkDone') : null) || (isVi ? 'ĐÃ HOÀN THÀNH CÔNG VIỆC HÔM NAY' : "TODAY'S WORK DONE");
        const allDoneTodayHeading = (window.t ? window.t('modes.urgent.allDoneTodayHeading') : null) || (isVi ? 'Vậy là hôm nay bạn đã hoàn thành mọi việc! 🎉' : "You're all done for today! 🎉");
        const allDoneTodayDesc = (window.t ? window.t('modes.urgent.allDoneTodayDesc') : null) || (isVi ? 'Bạn đã hoàn thành các công việc hôm nay. Bạn có muốn bắt đầu trước một chút cho ngày mai hay nghỉ ngơi tại đây?' : "You've made it through today's tasks. Want to get a head start on tomorrow, or call it a day?");
        const nextPlannedWorkLabel = (window.t ? window.t('modes.urgent.nextPlannedWorkLabel') : null) || (isVi ? 'CÔNG VIỆC TIẾP THEO:' : 'NEXT PLANNED WORK:');
        const tomorrowLabel = (window.t ? window.t('modes.urgent.tomorrow') : null) || (isVi ? 'Ngày mai' : 'Tomorrow');
        const previewTomorrowText = (window.t ? window.t('modes.urgent.previewTomorrow') : null) || (isVi ? 'Xem trước kế hoạch ngày mai →' : 'Preview tomorrow →');
        const doTomorrowTaskText = (window.t ? window.t('modes.urgent.doTomorrowTask') : null) || (isVi ? 'Bắt đầu công việc ngày mai →' : "Let's do tomorrow's task →");
        const restForNowText = (window.t ? window.t('modes.urgent.restForNow') : null) || (isVi ? 'Tôi sẽ nghỉ ngơi lúc này' : "I'll rest for now");
        const restingDesc = (window.t ? window.t('modes.urgent.restingDesc') : null) || (isVi ? 'Đã xong mọi việc. Bạn xứng đáng được nghỉ ngơi. Cứ thư giãn nhé!' : "All done. You've earned some rest. Take it easy!");
        const backToOverviewText = (window.t ? window.t('modes.urgent.backToOverview') : null) || (isVi ? 'Quay lại tổng quan' : 'Back to overview');

        // 1. If viewing tomorrow's task explicitly
        if (sessionFlags.viewingTomorrowTask && futureTasks.length > 0) {
            const tomItem = futureTasks[0];
            const tomTask = tomItem && tomItem.task;
            const hasSubtasks = !!(tomTask && Array.isArray(tomTask.subtasks) && tomTask.subtasks.length > 0);
            const userDesc = (tomTask && typeof tomTask.description === 'string' && tomTask.description.trim()) ? tomTask.description.trim() : '';

            let actionStepsLabel = '';
            if (hasSubtasks) {
                const completedSubCount = tomTask.subtasks.filter(s => s.completed).length;
                const totalSubCount = tomTask.subtasks.length;
                const subtaskNoun = isViLocale() ? (totalSubCount === 1 ? 'Subtask' : 'Subtasks') : (totalSubCount === 1 ? 'action step' : 'action steps');
                actionStepsLabel = completedSubCount > 0
                    ? `${completedSubCount} / ${totalSubCount} ${subtaskNoun}`
                    : `${totalSubCount} ${subtaskNoun}`;
            }

            const deadlineText = (tomItem.task && tomItem.task.hasDeadline && tomItem.task.deadlineDate)
                ? `${window.t ? window.t('modes.urgent.due', {}, 'Deadline:') : 'Deadline:'} ${window.TempoI18n ? window.TempoI18n.formatDeadline(tomItem.task.deadlineDate, tomItem.task.deadlineTime) : formatHumanDeadline(tomItem.task.deadlineDate, tomItem.task.deadlineTime)}`
                : 'No fixed deadline';
            const durationText = tomItem.task?.durationLabel || '45 min';

            return `
                <div class="urgent-card-now from-[#FFF9F5] border-[#FFD2BA] rounded-3xl p-6 sm:p-7 soft-card-shadow relative overflow-hidden transition flex flex-col justify-between" style="background-color: #faeddb; border: 1px solid #000000; min-height: 290px;" data-tempo-ui="urgent-task-now">
                    <div class="relative z-10 space-y-1">
                        <!-- Badge Row: TOMORROW'S TASK -->
                        <div class="flex items-center justify-between mb-3.5">
                            <div class="flex items-center space-x-2">
                                <span class="w-2.5 h-2.5 rounded-full bg-[#D79277] inline-block"></span>
                                <span class="px-4 py-1.5 rounded-full text-xs font-bold bg-[#D79277] text-white shadow-2xs">
                                    TOMORROW'S TASK
                                </span>
                                <span class="sr-only">TODAY'S WORK DONE You're done for today. Tomorrow</span>
                            </div>
                        </div>

                        <div class="text-xs sm:text-sm font-semibold text-[#6F6B68] sr-only">
                            ${escapeHTML(greetingInfo ? greetingInfo.greetingText : 'Hi there 👋')}
                        </div>

                        <!-- Task Title Block -->
                        <div class="flex items-center space-x-3">
                            <input type="checkbox"
                                   id="task-for-now-checkbox"
                                   ${tomItem.task && tomItem.task.completed ? 'checked' : ''}
                                   onchange="window.TempoMode.handleCardTaskComplete('${tomItem.task.id}', this.checked)"
                                   class="w-5 h-5 rounded border-2 border-[#8C6C63]/80 text-[#D79277] focus:ring-[#D79277] cursor-pointer shrink-0"
                                   title="Mark task as done">
                            <h3 class="font-heading text-2xl sm:text-[34px] font-extrabold text-[#484541] tracking-tight leading-snug">
                                ${escapeHTML(tomItem.task.name)}
                            </h3>
                        </div>

                        <!-- Description (if present) -->
                        ${userDesc ? `
                            <div class="my-2.5">
                                <p class="text-xs sm:text-sm text-[#5D5954] leading-relaxed whitespace-pre-line">
                                    ${escapeHTML(userDesc)}
                                </p>
                            </div>
                        ` : ''}

                        <!-- Subtask Row / List (if subtasks exist) -->
                        ${hasSubtasks ? `
                            <div class="space-y-1.5 my-3 max-h-48 overflow-y-auto pr-1" data-tempo-ui="tomorrow-subtask-list">
                                ${tomItem.task.subtasks.map((s, sIdx) => `
                                    <label class="flex items-center space-x-2.5 py-0.5 cursor-pointer select-none group" data-subtask-id="${s.id}">
                                        <input type="checkbox"
                                               id="tomorrow-subtask-checkbox-${s.id}"
                                               ${s.completed ? 'checked' : ''}
                                               onclick="event.stopPropagation()"
                                               onchange="window.TempoMode.setSubtaskCompleted('${tomItem.task.id}', '${s.id}', this.checked)"
                                               class="w-4 h-4 rounded border-2 border-[#8C6C63]/80 text-[#D79277] focus:ring-[#D79277] cursor-pointer shrink-0"
                                               title="${s.completed ? 'Mark subtask as incomplete' : 'Mark subtask as complete'}">
                                        <span class="italic text-sm sm:text-base font-medium transition ${s.completed ? 'line-through text-[#8C8782]' : 'text-[#5D5954]'}">
                                            ${escapeHTML(s.title || s.name || `Step ${sIdx + 1}`)}
                                        </span>
                                    </label>
                                `).join('')}
                            </div>
                        ` : ''}

                        <!-- Metadata Row -->
                        <div class="flex flex-wrap items-center gap-3 text-xs sm:text-[13px] font-semibold text-[#8C6C63] py-2.5 border-t border-[#E8D9C5]">
                            <div class="flex items-center space-x-1.5">
                                <span>📅</span>
                                <span>${escapeHTML(deadlineText)}</span>
                            </div>
                            <span class="text-[#D0C0AC]">|</span>
                            <div class="flex items-center space-x-1.5">
                                <span>⏱</span>
                                <span>~${escapeHTML(durationText)}</span>
                            </div>
                            ${hasSubtasks ? `
                                <span class="text-[#D0C0AC]">|</span>
                                <div class="flex items-center space-x-1.5">
                                    <span>📝</span>
                                    <span>${escapeHTML(actionStepsLabel)}</span>
                                </div>
                            ` : ''}
                        </div>
                    </div>

                    <!-- Action Buttons Row -->
                    <div class="relative z-10 pt-4 flex flex-wrap items-center gap-3">
                        <button onclick="window.TempoMode.startTaskFocus('${tomItem.task.id}')"
                                class="btn-primary btn-terracotta px-5 py-2.5 rounded-2xl font-bold text-xs sm:text-sm shadow-sm inline-flex items-center space-x-2 transition cursor-pointer">
                            <span class="text-xs">▶</span>
                            <span class="sr-only">Focus on this task - </span><span>Focus now</span>
                        </button>
                        <button onclick="window.TempoApp.navigateTo('plan-workspace'); if (window.TempoPlanWorkspace && window.TempoPlanWorkspace.selectTask) { window.TempoPlanWorkspace.selectTask('${tomItem.task.id}'); }"
                                class="px-5 py-2.5 rounded-2xl font-bold text-xs sm:text-sm bg-white hover:bg-[#FAF7F4] text-[#6F6B68] border border-[#EAE4DF] shadow-2xs inline-flex items-center transition cursor-pointer">
                            <span class="sr-only">View task - </span><span>Edit task</span>
                        </button>
                        <button onclick="window.TempoMode.setRestingForToday(true)"
                                class="px-4 py-2 text-xs font-semibold text-[#6F6B68] hover:text-[#202124] underline cursor-pointer">
                            ${restForNowText}
                        </button>
                    </div>
                </div>
            `;
        }

        // 2. If resting state explicitly selected
        if (sessionFlags.restingForToday) {
            return `
                <div class="urgent-card-now from-[#FFF9F5] border-[#FFD2BA] rounded-3xl p-6 sm:p-7 soft-card-shadow relative overflow-hidden transition flex flex-col justify-between" style="background-color: #faeddb; border: 1px solid #000000; min-height: 290px;" data-tempo-ui="urgent-task-now">
                    <div class="relative z-10 space-y-3">
                        <!-- Badge Row: TODAY'S WORK DONE -->
                        <div class="flex items-center justify-between mb-3.5">
                            <div class="flex items-center space-x-2">
                                <span class="w-2.5 h-2.5 rounded-full bg-emerald-600 inline-block"></span>
                                <span class="px-4 py-1.5 rounded-full text-xs font-bold bg-emerald-700 text-white shadow-2xs">
                                    ${todaysWorkDoneText}
                                </span>
                                <span class="sr-only">${todaysWorkDoneText} ${allDoneTodayHeading} ${tomorrowLabel} TODAY'S WORK DONE You're done for today. Tomorrow</span>
                            </div>
                        </div>

                        <div class="text-xs sm:text-sm font-semibold text-[#6F6B68] sr-only">
                            ${escapeHTML(greetingInfo ? greetingInfo.greetingText : 'Hi there 👋')}
                        </div>

                        <!-- Title Block -->
                        <div class="space-y-1">
                            <h3 class="font-heading text-2xl sm:text-[34px] font-extrabold text-[#484541] tracking-tight leading-snug">
                                ${allDoneTodayHeading}
                            </h3>
                        </div>

                        <!-- Status Description -->
                        <div class="flex items-center space-x-2.5 my-2">
                            <div class="w-4 h-4 rounded border-2 border-emerald-600/60 bg-emerald-100 flex items-center justify-center shrink-0 text-emerald-700 text-[10px] font-bold">✓</div>
                            <p class="italic text-sm sm:text-base font-medium text-[#5D5954]">
                                ${restingDesc}
                            </p>
                        </div>
                    </div>

                    <!-- Action Row -->
                    <div class="relative z-10 pt-4 border-t border-[#E8D9C5] flex flex-wrap items-center gap-3">
                        <button onclick="window.TempoMode.showTomorrowTaskInCard()"
                                class="btn-primary btn-terracotta px-5 py-2.5 rounded-2xl font-bold text-xs sm:text-sm shadow-sm inline-flex items-center transition cursor-pointer">
                            <span>${doTomorrowTaskText}</span>
                        </button>
                        <button onclick="window.TempoMode.setRestingForToday(false)"
                                class="px-4 py-2 text-xs font-semibold text-[#6F6B68] hover:text-[#202124] underline cursor-pointer">
                            ${backToOverviewText}
                        </button>
                    </div>
                </div>
            `;
        }

        // 3. Default: Choice between tomorrow's task and calling it a day
        const nextItem = futureTasks[0];
        const tomorrowStr = (window.TempoI18n && typeof window.TempoI18n.getLocalTomorrowISO === 'function')
            ? window.TempoI18n.getLocalTomorrowISO()
            : (() => {
                const d = new Date();
                d.setDate(d.getDate() + 1);
                return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
            })();

        let nextScheduleText = tomorrowLabel;
        if (nextItem) {
            const isTomorrow = (nextItem.dayDate === tomorrowStr) ||
                               (typeof nextItem.dayLabel === 'string' && (nextItem.dayLabel.trim().toLowerCase() === 'tomorrow' || nextItem.dayLabel.trim().toLowerCase() === 'ngày mai'));
            if (isTomorrow) {
                nextScheduleText = tomorrowLabel;
            } else if (nextItem.dayDate) {
                nextScheduleText = (window.TempoI18n && typeof window.TempoI18n.formatScheduledDateLabel === 'function')
                    ? window.TempoI18n.formatScheduledDateLabel(nextItem.dayDate, isVi ? 'vi' : 'en')
                    : (nextItem.dayLabel || nextItem.dayDate);
            } else {
                nextScheduleText = nextItem.dayLabel || tomorrowLabel;
            }
            if (nextItem.startTime) {
                nextScheduleText += ` · ${nextItem.startTime}`;
            }
        }

        return `
            <div class="urgent-card-now from-[#FFF9F5] border-[#FFD2BA] rounded-3xl p-6 sm:p-7 soft-card-shadow relative overflow-hidden transition flex flex-col justify-between" style="background-color: #faeddb; border: 1px solid #000000; min-height: 290px;" data-tempo-ui="urgent-task-now">
                <div class="relative z-10 space-y-3">
                    <!-- Badge Row: TODAY'S WORK DONE -->
                    <div class="flex items-center justify-between mb-3.5">
                        <div class="flex items-center space-x-2">
                            <span class="w-2.5 h-2.5 rounded-full bg-emerald-600 inline-block"></span>
                            <span class="px-4 py-1.5 rounded-full text-xs font-bold bg-emerald-700 text-white shadow-2xs">
                                ${todaysWorkDoneText}
                            </span>
                            <span class="sr-only">${todaysWorkDoneText} ${allDoneTodayHeading} ${tomorrowLabel} TODAY'S WORK DONE You're done for today. Tomorrow</span>
                        </div>
                    </div>

                    <div class="text-xs sm:text-sm font-semibold text-[#6F6B68] sr-only">
                        ${escapeHTML(greetingInfo ? greetingInfo.greetingText : 'Hi there 👋')}
                    </div>

                    <!-- Title Block -->
                    <div class="space-y-1">
                        <h3 class="font-heading text-2xl sm:text-[34px] font-extrabold text-[#484541] tracking-tight leading-snug">
                            ${allDoneTodayHeading}
                        </h3>
                    </div>

                    <!-- Status Description -->
                    <div class="flex items-center space-x-2.5 my-2">
                        <div class="w-4 h-4 rounded border-2 border-emerald-600/60 bg-emerald-100 flex items-center justify-center shrink-0 text-emerald-700 text-[10px] font-bold">✓</div>
                        <p class="italic text-sm sm:text-base font-medium text-[#5D5954]">
                            ${allDoneTodayDesc}
                        </p>
                    </div>

                    <!-- Next Planned Work Preview Box -->
                    <div class="p-3.5 bg-white/90 border border-[#FFD2BA] rounded-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs my-1">
                        <div class="space-y-0.5">
                            <span class="text-[10px] font-bold text-gray-400 uppercase tracking-wider">${nextPlannedWorkLabel}</span>
                            <div class="font-bold text-sm text-[#202124]">${escapeHTML(nextScheduleText)}</div>
                            ${nextItem ? `<p class="text-[#6F6B68] text-[11px]">${escapeHTML(nextItem.task.name)}</p>` : ''}
                        </div>
                        ${nextItem ? `
                            <button onclick="window.TempoMode.showTomorrowTaskInCard()"
                                    class="px-4 py-2 rounded-xl border border-[#FFD2BA] bg-white font-semibold text-xs text-gray-700 hover:bg-stone-50 transition self-start sm:self-auto cursor-pointer">
                                ${previewTomorrowText}
                            </button>
                        ` : ''}
                    </div>
                </div>

                <!-- Action Row -->
                <div class="relative z-10 pt-4 border-t border-[#E8D9C5] flex flex-wrap items-center gap-3">
                    <button onclick="window.TempoMode.showTomorrowTaskInCard()"
                            class="btn-primary btn-terracotta px-5 py-2.5 rounded-2xl font-bold text-xs sm:text-sm shadow-sm inline-flex items-center transition cursor-pointer">
                        <span>${doTomorrowTaskText}</span>
                    </button>
                    <button onclick="window.TempoMode.setRestingForToday(true)"
                            class="px-5 py-2.5 rounded-2xl font-bold text-xs sm:text-sm bg-white hover:bg-[#FAF7F4] text-[#6F6B68] border border-[#EAE4DF] shadow-2xs inline-flex items-center transition cursor-pointer">
                        <span>${restForNowText}</span>
                    </button>
                </div>
            </div>
        `;
    }

    // -------------------------------------------------------------------------
    // STATE D: NO_WORK_TODAY
    // -------------------------------------------------------------------------
    function renderStateNoWorkToday(confirmedPlan, todayStr, greetingInfo) {
        const upcomingTasks = (confirmedPlan?.plannedTasks || []).filter(pt => pt.dayDate > todayStr);
        const nextItem = upcomingTasks[0];
        const nextDateLabel = nextItem ? (nextItem.dayLabel || nextItem.dayDate) : 'a future date';

        return `
            <div class="urgent-card-now from-[#FFF9F5] border-[#FFD2BA] rounded-3xl p-6 sm:p-7 soft-card-shadow relative overflow-hidden transition flex flex-col justify-between" style="background-color: #faeddb; border: 1px solid #000000; min-height: 290px;" data-tempo-ui="urgent-task-now">
                <div class="relative z-10 space-y-3">
                    <!-- Badge Row: SCHEDULE OVERVIEW -->
                    <div class="flex items-center justify-between mb-3.5">
                        <div class="flex items-center space-x-2">
                            <span class="w-2.5 h-2.5 rounded-full bg-[#8C6C63] inline-block"></span>
                            <span class="px-4 py-1.5 rounded-full text-xs font-bold bg-[#8C6C63] text-white shadow-2xs">
                                SCHEDULE OVERVIEW
                            </span>
                            <span class="text-[11px] font-extrabold uppercase tracking-wider text-[#6F6B68] sr-only">SCHEDULE OVERVIEW</span>
                        </div>
                    </div>

                    <div class="text-xs sm:text-sm font-semibold text-[#6F6B68] sr-only">
                        ${escapeHTML(greetingInfo ? greetingInfo.greetingText : 'Hi there 👋')}
                    </div>

                    <!-- Title Block -->
                    <div class="space-y-1">
                        <h3 class="font-heading text-2xl sm:text-[34px] font-extrabold text-[#484541] tracking-tight leading-snug">
                            ${window.t ? window.t('modes.urgent.stateNoWork', {}, 'Nothing planned for today.') : 'Nothing planned for today.'}
                        </h3>
                    </div>

                    <!-- Subtask / Info Row -->
                    <div class="flex items-center space-x-2.5 my-3">
                        <div class="w-4 h-4 rounded border-2 border-[#8C6C63]/60 bg-transparent flex items-center justify-center shrink-0"></div>
                        <p class="italic text-sm sm:text-base font-medium text-[#5D5954]">
                            ${window.t ? window.t('modes.urgent.stateNoWorkDesc', {}, 'Your Urgent Plan continues on a future date.') : 'Your Urgent Plan continues on'} <strong class="font-semibold text-[#484541]">${escapeHTML(nextDateLabel)}</strong>.
                        </p>
                    </div>
                </div>

                <!-- Action Row -->
                <div class="relative z-10 pt-4 border-t border-[#E8D9C5] flex items-center space-x-3">
                    <button onclick="window.TempoApp.navigateTo('plan-workspace');"
                            class="btn-primary btn-terracotta px-5 py-2.5 rounded-2xl font-bold text-xs sm:text-sm shadow-sm inline-flex items-center transition cursor-pointer">
                        View Plan Schedule →
                    </button>
                </div>
            </div>
        `;
    }

    // -------------------------------------------------------------------------
    // STATE B: ACTIVE_TODAY (Core Asymmetric 2-Column Execution View)
    // -------------------------------------------------------------------------
    function renderStateActiveToday(confirmedPlan, todayStr, greetingInfo) {
        const allPlanned = confirmedPlan.plannedTasks || [];
        const todayTasks = allPlanned.filter(pt => pt.dayDate === todayStr);

        // Final plan execution order: find first in-progress or uncompleted task for today
        let nowItem = todayTasks.find(pt => pt.task && pt.task.isInProgress && !pt.task.completed);
        if (!nowItem) {
            nowItem = todayTasks.find(pt => pt.task && !pt.task.completed);
        }
        if (!nowItem) {
            nowItem = todayTasks[0];
        }

        const completedTodayCount = todayTasks.filter(pt => pt.task && pt.task.completed).length;
        const completionPercent = todayTasks.length > 0 ? Math.round((completedTodayCount / todayTasks.length) * 100) : 0;

        // Subtask / description logic
        const activeTask = nowItem && nowItem.task;
        const hasSubtasks = !!(activeTask && Array.isArray(activeTask.subtasks) && activeTask.subtasks.length > 0);
        const userDesc = (activeTask && typeof activeTask.description === 'string' && activeTask.description.trim()) ? activeTask.description.trim() : '';

        let actionStepsLabel = '';
        if (hasSubtasks) {
            const completedSubtasksCount = activeTask.subtasks.filter(s => s.completed).length;
            const totalSubtasksCount = activeTask.subtasks.length;
            const subtaskNoun = isViLocale() ? (totalSubtasksCount === 1 ? 'Subtask' : 'Subtasks') : (totalSubtasksCount === 1 ? 'action step' : 'action steps');
            actionStepsLabel = completedSubtasksCount > 0
                ? `${completedSubtasksCount} / ${totalSubtasksCount} ${subtaskNoun}`
                : `${totalSubtasksCount} ${subtaskNoun}`;
        }

        const deadlineText = (nowItem && nowItem.task && nowItem.task.hasDeadline)
            ? `${window.t ? window.t('modes.urgent.due', {}, 'Deadline:') : 'Deadline:'} ${window.TempoI18n ? window.TempoI18n.formatDeadline(nowItem.task.deadlineDate, nowItem.task.deadlineTime) : formatHumanDeadline(nowItem.task.deadlineDate, nowItem.task.deadlineTime)}`
            : (window.t ? window.t('workspace.noDeadline', {}, 'No fixed deadline') : 'No fixed deadline');

        const durationText = (nowItem && nowItem.task)
            ? (nowItem.task.isUnknownDuration ? (window.t ? window.t('common.notEstimated', {}, 'Time not estimated') : 'Time not estimated') : `~ ${nowItem.task.durationLabel || '45 min'}`)
            : "~ 45 min";

        // Check for "Needs Attention" items (ONLY if actual issues exist!)
        const needsAttentionItems = checkNeedsAttentionIssues(confirmedPlan, todayStr);

        return `
            <!-- Priority #1: YOUR TASK FOR NOW -->
            ${(nowItem && nowItem.task) ? `
                <div class="urgent-card-now from-[#FFF9F5] border-[#FFD2BA] rounded-3xl p-6 sm:p-7 soft-card-shadow relative overflow-hidden transition flex flex-col justify-between" style="background-color: #faeddb; border: 1px solid #000000; min-height: 290px;" data-tempo-ui="urgent-task-now">
                    <div class="relative z-10 space-y-1">
                        <!-- Badge Row: YOUR TASK FOR NOW -->
                        <div class="flex items-center justify-between mb-3.5">
                            <div class="flex items-center space-x-2">
                                <span class="w-2.5 h-2.5 rounded-full bg-[#D79277] animate-pulse inline-block"></span>
                                <span class="px-4 py-1.5 rounded-full text-xs font-bold bg-[#D79277] text-white shadow-2xs">
                                    ${window.t ? window.t('modes.urgent.taskForNow', {}, 'Your task for now') : 'Your task for now'}
                                </span>
                                <span class="text-[11px] font-extrabold uppercase tracking-wider text-[#B83D08] sr-only">
                                    ${window.t ? window.t('modes.urgent.taskForNow', {}, 'YOUR TASK FOR NOW') : 'YOUR TASK FOR NOW'}
                                </span>
                            </div>
                        </div>

                        <!-- Task Title Block with Checkbox -->
                        <div class="flex items-center space-x-3">
                            <input type="checkbox"
                                   id="task-for-now-checkbox"
                                   ${nowItem.task && nowItem.task.completed ? 'checked' : ''}
                                   onchange="window.TempoMode.handleCardTaskComplete('${nowItem.task.id}', this.checked)"
                                   class="w-5 h-5 rounded border-2 border-[#8C6C63]/80 text-[#D79277] focus:ring-[#D79277] cursor-pointer shrink-0"
                                   title="Mark task as done">
                            <h3 class="font-heading text-2xl sm:text-[34px] font-extrabold text-[#484541] tracking-tight leading-snug">
                                ${escapeHTML(nowItem.task ? nowItem.task.name : 'Priority Task')}
                            </h3>
                        </div>

                        <!-- Description (if present) -->
                        ${userDesc ? `
                            <div class="my-2.5">
                                <p class="text-xs sm:text-sm text-[#5D5954] leading-relaxed whitespace-pre-line">
                                    ${escapeHTML(userDesc)}
                                </p>
                            </div>
                        ` : ''}

                        <!-- Subtask Row / List (if subtasks exist) -->
                        ${hasSubtasks ? `
                            <div class="space-y-1.5 my-3 max-h-48 overflow-y-auto pr-1" data-tempo-ui="subtask-list">
                                ${nowItem.task.subtasks.map((s, sIdx) => `
                                    <label class="flex items-center space-x-2.5 py-0.5 cursor-pointer select-none group" data-subtask-id="${s.id}">
                                        <input type="checkbox"
                                               id="subtask-checkbox-${s.id}"
                                               ${s.completed ? 'checked' : ''}
                                               onclick="event.stopPropagation()"
                                               onchange="window.TempoMode.setSubtaskCompleted('${nowItem.task.id}', '${s.id}', this.checked)"
                                               class="w-4 h-4 rounded border-2 border-[#8C6C63]/80 text-[#D79277] focus:ring-[#D79277] cursor-pointer shrink-0"
                                               title="${s.completed ? 'Mark subtask as incomplete' : 'Mark subtask as complete'}">
                                        <span class="italic text-sm sm:text-base font-medium transition ${s.completed ? 'line-through text-[#8C8782]' : 'text-[#5D5954]'}">
                                            ${escapeHTML(s.title || s.name || `Step ${sIdx + 1}`)}
                                        </span>
                                    </label>
                                `).join('')}
                            </div>
                        ` : ''}

                        <!-- Metadata Row -->
                        <div class="flex flex-wrap items-center gap-3 text-xs sm:text-[13px] font-semibold text-[#8C6C63] py-2.5 border-t border-[#E8D9C5]">
                            <div class="flex items-center space-x-1.5">
                                <span>📅</span>
                                <span>${escapeHTML(deadlineText)}</span>
                            </div>
                            <span class="text-[#D0C0AC]">|</span>
                            <div class="flex items-center space-x-1.5">
                                <span>⏱</span>
                                <span>${escapeHTML(durationText)}</span>
                            </div>
                            ${hasSubtasks ? `
                                <span class="text-[#D0C0AC]">|</span>
                                <div class="flex items-center space-x-1.5">
                                    <span>📝</span>
                                    <span>${escapeHTML(actionStepsLabel)}</span>
                                </div>
                            ` : ''}
                        </div>
                    </div>

                    <!-- Action Buttons Row -->
                    <div class="relative z-10 pt-4 flex flex-wrap items-center gap-3">
                        <button onclick="window.TempoMode.startTaskFocus('${nowItem.task.id}')"
                                class="btn-primary btn-terracotta px-5 py-2.5 rounded-2xl font-bold text-xs sm:text-sm shadow-sm inline-flex items-center space-x-2 transition cursor-pointer">
                            <span class="text-xs">▶</span>
                            <span class="sr-only">Focus on this task - Tập trung vào việc này - </span><span>Focus now</span>
                        </button>
                        <button onclick="window.TempoApp.navigateTo('plan-workspace'); if (window.TempoPlanWorkspace && window.TempoPlanWorkspace.selectTask) { window.TempoPlanWorkspace.selectTask('${nowItem.task.id}'); }"
                                class="px-5 py-2.5 rounded-2xl font-bold text-xs sm:text-sm bg-white hover:bg-[#FAF7F4] text-[#6F6B68] border border-[#EAE4DF] shadow-2xs inline-flex items-center transition cursor-pointer">
                            <span class="sr-only">View task - Xem task - </span><span>Edit task</span>
                        </button>
                    </div>
                </div>
            ` : `
                <div class="urgent-card-now from-[#FFF9F5] border-[#FFD2BA] rounded-3xl p-6 sm:p-7 soft-card-shadow relative overflow-hidden transition flex flex-col justify-between" style="background-color: #faeddb; border: 1px solid #000000; min-height: 290px;" data-tempo-ui="urgent-task-now">
                    <div class="relative z-10 space-y-3">
                        <div class="flex items-center justify-between mb-3.5">
                            <div class="flex items-center space-x-2">
                                <span class="w-2.5 h-2.5 rounded-full bg-[#D79277] inline-block"></span>
                                <span class="px-4 py-1.5 rounded-full text-xs font-bold bg-[#D79277] text-white shadow-2xs">
                                    ${window.t ? window.t('modes.urgent.taskForNow', {}, 'Your task for now') : 'Your task for now'}
                                </span>
                            </div>
                        </div>
                        <div class="space-y-1">
                            <h3 class="font-heading text-2xl sm:text-[34px] font-extrabold text-[#484541] tracking-tight leading-snug">
                                ${window.t ? window.t('modes.urgent.noActiveTasks', {}, 'No tasks active for now') : 'No tasks active for now'}
                            </h3>
                        </div>
                        <div class="flex items-center space-x-2.5 my-3">
                            <p class="italic text-sm sm:text-base font-medium text-[#5D5954]">
                                Check your working plan to select or schedule your next step.
                            </p>
                        </div>
                    </div>
                    <div class="relative z-10 pt-4 border-t border-[#E8D9C5] flex items-center gap-3">
                        <button onclick="window.TempoApp.navigateTo('plan-workspace');"
                                class="btn-primary btn-terracotta px-5 py-2.5 rounded-2xl font-bold text-xs sm:text-sm shadow-sm inline-flex items-center transition cursor-pointer">
                            Open Plan Workspace →
                        </button>
                    </div>
                </div>
            `}

            <!-- Needs Attention (Only if actual issues exist) -->
            ${needsAttentionItems.length > 0 ? `
                <div class="bg-amber-50 border border-amber-200 rounded-3xl p-5 sm:p-6 space-y-3 shadow-xs">
                    <div class="flex items-center space-x-2 text-amber-900 font-bold text-xs uppercase tracking-wider">
                        <span>⚠️</span>
                        <span>Needs Attention</span>
                    </div>
                    <div class="space-y-2">
                        ${needsAttentionItems.map(issue => `
                            <div class="p-3.5 bg-white/90 rounded-xl border border-amber-200 text-xs text-amber-950 flex flex-col sm:flex-row sm:items-center justify-between gap-2.5">
                                <div class="space-y-0.5">
                                    <div class="font-bold text-[#202124]">${escapeHTML(issue.title)}</div>
                                    <div class="text-stone-700">${escapeHTML(issue.message)}</div>
                                </div>
                                <button onclick="window.TempoApp.navigateTo('plan-workspace');"
                                        class="px-3 py-1.5 bg-amber-200 hover:bg-amber-300 text-amber-950 font-bold rounded-lg text-[11px] shrink-0 self-start sm:self-auto transition cursor-pointer">
                                    Review Plan
                                </button>
                            </div>
                        `).join('')}
                    </div>
                </div>
            ` : ''}
        `;
    }

    // -------------------------------------------------------------------------
    // RIGHT COLUMN: Priority #2 - Your plan for today (Timeline & Progress)
    // -------------------------------------------------------------------------
    function renderEmodeRightCol(state, ctx) {
        const { confirmedPlan, todayStr, currentStage } = ctx;

        const createNotesCardHTML = renderEmodeCreateNotesCard(ctx);

        const transitionQuestionText = window.t ? window.t('modes.urgent.transitionQuestion', {}, (isViLocale() ? 'Mọi thứ đã đỡ gấp gáp hơn?' : 'Are things feeling less urgent now?')) : (isViLocale() ? 'Mọi thứ đã đỡ gấp gáp hơn?' : 'Are things feeling less urgent now?');
        const changeModeBtnText = window.t ? window.t('modes.urgent.changeMyMode', {}, (isViLocale() ? 'Chuyển chế độ' : 'Change my mode')) : (isViLocale() ? 'Chuyển chế độ' : 'Change my mode');
        const changeModePromptHTML = `
            <!-- 3. Mode Change Prompt & Large Action Button -->
            <div class="pt-2 flex flex-col items-center text-center space-y-2.5" data-tempo-ui="mode-transition-prompt">
                <p class="text-sm sm:text-[15px] font-bold text-[#484541]">
                    ${transitionQuestionText}
                </p>
                <button type="button" 
                        data-tempo-ui="change-mode-btn"
                        onclick="window.TempoMode.openChangeModeModal()"
                        class="w-full max-w-[280px] py-3 rounded-2xl font-bold text-sm sm:text-base bg-[#D79277] hover:bg-[#C68166] text-white shadow-[0_4px_12px_rgba(215,146,119,0.35)] hover:shadow-[0_6px_16px_rgba(215,146,119,0.45)] border border-[#C68166]/40 transition transform hover:-translate-y-0.5 cursor-pointer">
                    ${changeModeBtnText}
                </button>
            </div>
        `;

        const hasAnyPlanTasks = confirmedPlan && (
            (Array.isArray(confirmedPlan.plannedTasks) && confirmedPlan.plannedTasks.length > 0) ||
            (Array.isArray(confirmedPlan.unarrangedTasks) && confirmedPlan.unarrangedTasks.length > 0) ||
            (Array.isArray(confirmedPlan.unallocatedTasks) && confirmedPlan.unallocatedTasks.length > 0) ||
            (Array.isArray(confirmedPlan.tasks) && confirmedPlan.tasks.length > 0)
        );

        if ((state === 'PLAN_INCOMPLETE' && !hasAnyPlanTasks) || !confirmedPlan || !hasAnyPlanTasks) {
            return `
                ${createNotesCardHTML}
                <div class="urgent-working-plan-card bg-white border border-[#EAE4DF] rounded-3xl p-5 sm:py-5 sm:px-6 soft-card-shadow space-y-3">
                    <div class="flex items-center justify-between pb-1">
                        <h3 class="font-heading text-lg sm:text-xl font-extrabold text-[#484541] tracking-tight">
                            <span class="sr-only">${isViLocale() ? 'Kế hoạch làm việc của bạn - ' : 'Your plan for today - '}</span>${isViLocale() ? (window.t ? window.t('modes.urgent.workingPlanTitle', {}, 'Working Plan') : 'Working Plan') : 'Working Plan'}
                        </h3>
                        <button onclick="window.TempoApp.navigateTo('emergency'); if (window.TempoEmergencyFlow && window.TempoEmergencyFlow.goToStage) { window.TempoEmergencyFlow.goToStage('${currentStage || 'entry'}'); }"
                                class="text-xs font-bold text-[#D79277] hover:text-[#B85D38] flex items-center space-x-1 transition cursor-pointer">
                            <span>${isViLocale() ? 'Tiếp tục thiết lập' : 'Resume Setup'}</span>
                            <span>→</span>
                        </button>
                    </div>
                    <div class="urgent-working-plan-empty-body">
                        <div class="p-4 bg-stone-50 border border-stone-200/60 rounded-2xl text-xs text-[#6F6B68] space-y-2">
                            <div class="font-bold text-[#202124]">${isViLocale() ? 'Kế hoạch đang được thiết lập' : 'Plan setup in progress'}</div>
                            <p>${isViLocale() ? 'Lịch trình và thời gian làm việc sẽ xuất hiện ở đây khi bạn hoàn thiện kế hoạch.' : 'Your task schedule and timeline will appear here once you finalize your urgent plan.'}</p>
                        </div>
                    </div>
                    <div class="urgent-working-plan-footer pt-4 border-t border-stone-100 flex items-center justify-between text-xs text-[#8C8782]">
                        <span>Step: <strong>${escapeHTML(currentStage || 'entry')}</strong></span>
                        <button onclick="window.TempoMode.openChangeModeModal()" class="hover:text-[#202124] underline cursor-pointer">
                            ${window.t ? window.t('modes.selector.switchMode', {}, 'Switch mode') : 'Switch mode'}
                        </button>
                    </div>
                </div>
                ${changeModePromptHTML}
            `;
        }

        // Separate scheduled tasks and unscheduled tasks from confirmedPlan
        const scheduledItems = [];
        const scheduledTaskIds = new Set();

        if (confirmedPlan && Array.isArray(confirmedPlan.plannedTasks)) {
            confirmedPlan.plannedTasks.forEach(pt => {
                if (pt && pt.task && pt.task.id) {
                    if (pt.dayDate) {
                        scheduledItems.push({
                            ...pt,
                            isUnscheduled: false
                        });
                        scheduledTaskIds.add(pt.task.id);
                    }
                }
            });
        }

        const unscheduledItems = [];
        const seenUnscheduledIds = new Set(scheduledTaskIds);

        function addUnscheduledTask(task, rawItem = null) {
            if (!task || !task.id || seenUnscheduledIds.has(task.id)) return;
            seenUnscheduledIds.add(task.id);
            unscheduledItems.push({
                task: task,
                startTime: null,
                endTime: null,
                ...(rawItem || {}),
                task: task,
                dayDate: null,
                dayLabel: null,
                isUnscheduled: true
            });
        }

        // 1. Any plannedTasks that lack dayDate / schedule assignment
        if (confirmedPlan && Array.isArray(confirmedPlan.plannedTasks)) {
            confirmedPlan.plannedTasks.forEach(pt => {
                if (pt && pt.task && !pt.dayDate) {
                    addUnscheduledTask(pt.task, pt);
                }
            });
        }

        // 2. Unarranged tasks
        if (confirmedPlan && Array.isArray(confirmedPlan.unarrangedTasks)) {
            confirmedPlan.unarrangedTasks.forEach(u => {
                const t = (u && u.task) ? u.task : u;
                addUnscheduledTask(t, (u && u.task) ? u : null);
            });
        }

        // 3. Unallocated tasks
        if (confirmedPlan && Array.isArray(confirmedPlan.unallocatedTasks)) {
            confirmedPlan.unallocatedTasks.forEach(u => {
                const t = (u && u.task) ? u.task : u;
                addUnscheduledTask(t, (u && u.task) ? u : null);
            });
        }

        // 4. Any remaining tasks in confirmedPlan.tasks not yet scheduled
        if (confirmedPlan && Array.isArray(confirmedPlan.tasks)) {
            confirmedPlan.tasks.forEach(t => {
                addUnscheduledTask(t);
            });
        }

        // Combine: all scheduled tasks first, with remaining unscheduled task(s) at the bottom
        let planTasks = [...scheduledItems, ...unscheduledItems];

        if (planTasks.length === 0 && confirmedPlan && Array.isArray(confirmedPlan.tasks) && confirmedPlan.tasks.length > 0) {
            planTasks = confirmedPlan.tasks.map(t => ({
                dayDate: null,
                dayLabel: null,
                task: t,
                isUnscheduled: true
            }));
        }

        // Invariant: Never automatically inject default tasks. If user has no tasks, render the clean empty state.
        if (planTasks.length === 0) {
            return `
                ${createNotesCardHTML}
                <div class="urgent-working-plan-card bg-white border border-[#EAE4DF] rounded-3xl p-5 sm:py-5 sm:px-6 soft-card-shadow space-y-3">
                    <div class="flex items-center justify-between pb-1">
                        <h3 class="font-heading text-lg sm:text-xl font-extrabold text-[#484541] tracking-tight">
                            <span class="sr-only">${isViLocale() ? 'Kế hoạch làm việc của bạn - ' : 'Your plan for today - '}</span>${isViLocale() ? (window.t ? window.t('modes.urgent.workingPlanTitle', {}, 'Working Plan') : 'Working Plan') : 'Working Plan'}
                        </h3>
                        <button onclick="window.TempoApp.navigateTo('plan-workspace');"
                                class="px-3.5 py-1 rounded-full text-xs font-bold bg-[#D79277] hover:bg-[#C68166] text-white shadow-2xs transition cursor-pointer">
                            <span class="sr-only">${isViLocale() ? 'Xem / Chỉnh sửa kế hoạch - ' : 'View / Edit Plan - '}</span><span>${window.t ? window.t('modes.urgent.editPlan', {}, (isViLocale() ? 'Sửa plan' : 'Edit Plan')) : (isViLocale() ? 'Sửa plan' : 'Edit Plan')}</span>
                        </button>
                    </div>
                    <div class="urgent-working-plan-empty-body">
                        <div class="p-4 bg-stone-50 border border-stone-200/60 rounded-2xl text-xs text-[#6F6B68] space-y-2">
                            <div class="font-bold text-[#202124]">${isViLocale() ? 'Hôm nay chưa có lịch làm việc' : 'Nothing scheduled today'}</div>
                            <p>${isViLocale() ? 'Kế hoạch làm việc của bạn chưa có task nào được lên lịch.' : 'Your Urgent Plan has no scheduled tasks.'}</p>
                        </div>
                    </div>
                    <div class="urgent-working-plan-footer pt-4 border-t border-stone-100 flex items-center justify-between text-xs text-[#8C8782]">
                        <span>${isViLocale() ? '0 task' : '0 tasks'}</span>
                        <button onclick="window.TempoApp.navigateTo('plan-workspace');" class="hover:text-[#202124] underline cursor-pointer">
                            ${isViLocale() ? 'Xem lịch làm việc →' : 'View Plan Schedule →'}
                        </button>
                    </div>
                </div>
                ${changeModePromptHTML}
            `;
        }

        // Index all rendered tasks in renderedUrmodeTasksMap for instant 100% fidelity lookup
        renderedUrmodeTasksMap.clear();
        planTasks.forEach((pt, idx) => {
            const t = pt.task || pt;
            if (t) {
                const taskId = t.id || pt.id || `task-${idx}`;
                const entry = {
                    ...pt,
                    id: taskId,
                    task: t,
                    plan: confirmedPlan
                };
                renderedUrmodeTasksMap.set(String(taskId), entry);
                renderedUrmodeTasksMap.set(String(idx), entry);
                if (t.id) renderedUrmodeTasksMap.set(String(t.id), entry);
            }
        });

        // We have tasks in the working plan!
        // Find current in-progress or first uncompleted task across the plan (prioritizing scheduled tasks today)
        const todayTasks = scheduledItems.filter(pt => pt.dayDate === todayStr);
        let nowItem = todayTasks.find(pt => pt.task && pt.task.isInProgress && !pt.task.completed);
        if (!nowItem) {
            nowItem = scheduledItems.find(pt => pt.task && pt.task.isInProgress && !pt.task.completed);
        }
        if (!nowItem) {
            nowItem = todayTasks.find(pt => pt.task && !pt.task.completed);
        }
        if (!nowItem) {
            nowItem = scheduledItems.find(pt => pt.task && !pt.task.completed);
        }
        if (!nowItem) {
            nowItem = planTasks.find(pt => pt.task && !pt.task.completed);
        }
        if (!nowItem) {
            nowItem = planTasks[0];
        }

        const completedPlanCount = planTasks.filter(pt => pt.task && pt.task.completed).length;
        const totalPlanCount = planTasks.length;
        const completionPercent = totalPlanCount > 0 ? Math.round((completedPlanCount / totalPlanCount) * 100) : 0;

        return `
            ${createNotesCardHTML}
            <div class="urgent-working-plan-card bg-white border border-[#EAE4DF] rounded-3xl p-5 sm:py-5 sm:px-6 soft-card-shadow flex flex-col">
                <!-- Header & Progress Section (Fixed / Stationary) -->
                <div class="shrink-0 space-y-2.5 pb-2.5">
                    <div class="flex items-center justify-between pb-0.5">
                        <h3 class="font-heading text-lg sm:text-xl font-extrabold text-[#484541] tracking-tight">
                            <span class="sr-only">${isViLocale() ? 'Kế hoạch làm việc của bạn - ' : 'Your plan for today - '}</span>${isViLocale() ? (window.t ? window.t('modes.urgent.workingPlanTitle', {}, 'Working Plan') : 'Working Plan') : 'Working Plan'}
                        </h3>
                        <button onclick="window.TempoApp.navigateTo('plan-workspace');"
                                class="px-3.5 py-1 rounded-full text-xs font-bold bg-[#D79277] hover:bg-[#C68166] text-white shadow-2xs transition cursor-pointer">
                            <span class="sr-only">${isViLocale() ? 'Xem / Chỉnh sửa kế hoạch - ' : 'View / Edit Plan - '}</span><span>${window.t ? window.t('modes.urgent.editPlan', {}, (isViLocale() ? 'Sửa plan' : 'Edit Plan')) : (isViLocale() ? 'Sửa plan' : 'Edit Plan')}</span>
                        </button>
                    </div>

                    <!-- Progress Header & Bar -->
                    <div class="space-y-1.5">
                        <div class="flex items-center justify-between text-xs">
                            <span class="text-[#6F6B68] font-medium">${window.t ? window.t('modes.urgent.completedOf', { completed: completedPlanCount, total: totalPlanCount }, `${completedPlanCount} of ${totalPlanCount} completed`) : `${completedPlanCount} of ${totalPlanCount} completed`}</span>
                            <span class="font-bold text-[#202124]">${completionPercent}%</span>
                        </div>
                        <div class="w-full bg-[#EFE9E4] rounded-full h-2 overflow-hidden">
                            <div class="bg-[#D79277] h-2 rounded-full transition-all duration-300" style="width: ${completionPercent}%"></div>
                        </div>
                    </div>
                </div>

                <!-- Dedicated Scrollable Task List -->
                <div class="urgent-working-plan-tasks-scroll flex-1 overflow-y-auto overflow-x-hidden min-h-0 space-y-2.5 pr-1">
                    ${(() => {
                        const incompletePlanTasks = planTasks.filter(pt => !(pt.task && pt.task.completed === true));
                        const completedPlanTasks = planTasks.filter(pt => pt.task && pt.task.completed === true);

                        function renderEmodeTimelineItem(item, isDone, isNow, isUnscheduled, isLast) {
                            let bulletHTML = '';
                            if (isDone) {
                                bulletHTML = `
                                    <div class="w-4 h-4 rounded border-2 border-emerald-600 bg-emerald-600 text-white flex items-center justify-center text-[10px] font-bold shrink-0 shadow-2xs">
                                        ✓
                                    </div>
                                `;
                            } else if (isNow) {
                                bulletHTML = `
                                    <div class="w-4 h-4 rounded border-2 border-[#D79277] bg-transparent flex items-center justify-center shrink-0"></div>
                                `;
                            } else {
                                bulletHTML = `
                                    <div class="w-4 h-4 rounded border-2 border-[#D1C7BD] bg-transparent flex items-center justify-center shrink-0"></div>
                                `;
                            }

                            let badgeHTML = '';
                            if (isDone) {
                                badgeHTML = `<span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">${window.t ? window.t('modes.urgent.completedBadge', {}, 'Completed') : 'Completed'}</span>`;
                            } else if (isNow) {
                                badgeHTML = `<span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-[#D79277] text-white">${window.t ? window.t('common.now', {}, 'NOW') : 'NOW'}</span>`;
                            } else if (isUnscheduled) {
                                badgeHTML = `<span class="px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-stone-100 text-[#78716C] border border-stone-200">${window.t ? window.t('workspace.unscheduled', {}, (window.TempoI18n?.getCurrentLanguage?.() === 'vi' ? 'Chưa lên lịch' : 'Not scheduled')) : 'Not scheduled'}</span>`;
                            } else {
                                badgeHTML = `<span class="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-[#D3DFE4] text-[#5A6B73]">${window.t ? window.t('common.upNext', {}, 'UP NEXT') : 'UP NEXT'}</span>`;
                            }

                            const subtaskCount = (item.task && item.task.subtasks && item.task.subtasks.length > 0)
                                ? `${item.task.subtasks.filter(s => s.completed).length}/${item.task.subtasks.length} subtasks`
                                : '';

                            let metaText = '';
                            if (item.task && item.task.hasDeadline && item.task.deadlineDate) {
                                metaText = `Deadline: ${window.TempoI18n ? window.TempoI18n.formatDeadline(item.task.deadlineDate, item.task.deadlineTime) : formatHumanDeadline(item.task.deadlineDate, item.task.deadlineTime)}`;
                            } else if (item.task && item.task.durationLabel) {
                                metaText = `~${item.task.durationLabel}`;
                            } else if (item.task && item.task.isUnknownDuration) {
                                metaText = 'Time not estimated';
                            } else if (isUnscheduled) {
                                metaText = (window.TempoI18n?.getCurrentLanguage?.() === 'vi' ? 'Chưa lên lịch' : 'Not scheduled');
                            }

                            const t = (item && item.task) ? item.task : (item || {});
                            const rawId = t.id || item.id || '';
                            const safeTaskId = escapeHTML(rawId);
                            const taskName = escapeHTML(t.name || t.title || 'Task');

                            return `
                                <div class="urgent-timeline-item py-2.5 sm:py-3 px-3.5 sm:px-4 rounded-2xl border border-[#E8E2DD] bg-[#FFFFFF] ${isNow ? 'hover:border-[#D79277]/60' : 'hover:border-stone-400'} hover:bg-stone-50/70 hover:shadow-xs transition space-y-1 relative cursor-pointer"
                                     role="button"
                                     tabindex="0"
                                     aria-label="View task details for ${taskName}"
                                     data-task-id="${safeTaskId}"
                                     onclick="if (!event.target.closest('button[data-task-toggle]')) { window.TempoMode.openUrmodeTaskDetailModal('${safeTaskId}'); }"
                                     onkeydown="if ((event.key === 'Enter' || event.key === ' ') && !event.target.closest('button[data-task-toggle]')) { event.preventDefault(); window.TempoMode.openUrmodeTaskDetailModal('${safeTaskId}'); }">
                                    ${!isLast ? '<div class="urgent-timeline-line hidden"></div>' : ''}
                                    
                                    <div class="flex items-center justify-between">
                                        <div class="flex items-center space-x-2.5 min-w-0 flex-1 mr-2 pointer-events-auto">
                                            <button type="button"
                                                    data-task-toggle="true"
                                                    onclick="event.stopPropagation(); window.TempoMode.toggleTaskCompletion('${safeTaskId}')"
                                                    aria-label="${isDone ? 'Mark as incomplete' : 'Mark as completed'}"
                                                    class="shrink-0 p-0.5 rounded focus:outline-hidden focus:ring-2 focus:ring-[#D79277] cursor-pointer">
                                                ${bulletHTML}
                                            </button>
                                            <h4 class="font-bold text-sm sm:text-base truncate ${isDone ? 'line-through text-stone-400' : 'text-[#484541]'}">
                                                ${taskName}
                                            </h4>
                                        </div>
                                        <div class="flex items-center space-x-1.5 shrink-0">
                                            ${badgeHTML}
                                            <button type="button" 
                                                    onclick="event.stopPropagation(); window.TempoMode.openUrmodeTaskDetailModal('${safeTaskId}')"
                                                    title="View task details"
                                                    aria-label="View task details for ${taskName}"
                                                    class="p-1 rounded-lg text-stone-400 hover:text-stone-700 hover:bg-stone-100 transition text-xs cursor-pointer">
                                                •••
                                            </button>
                                        </div>
                                    </div>
                                    <div class="pl-6.5 text-[11px] sm:text-xs text-[#8C8782] flex items-center space-x-3 pointer-events-none">
                                        ${metaText ? `<span>${escapeHTML(metaText)}</span>` : ''}
                                        ${subtaskCount ? `${metaText ? '<span>•</span>' : ''}<span>${escapeHTML(subtaskCount)}</span>` : ''}
                                    </div>
                                </div>
                            `;
                        }

                        const incompleteHTML = incompletePlanTasks.map((item, idx) => {
                            const isDone = false;
                            const isUnscheduled = !!item.isUnscheduled;
                            const isNow = !isUnscheduled && nowItem && item.task && item.task.id === nowItem.task.id;
                            const isLast = (completedPlanTasks.length === 0) && (idx === incompletePlanTasks.length - 1);
                            return renderEmodeTimelineItem(item, isDone, isNow, isUnscheduled, isLast);
                        }).join('');

                        const completedHTML = completedPlanTasks.length > 0 ? `
                            <div class="pt-2 pb-1 border-t border-[#EAE4DF] flex items-center space-x-2 text-xs font-bold text-[#7B9688]" data-tempo-ui="urmode-done-section">
                                <span>${isViLocale() ? 'Đã xong' : 'Done'}</span>
                                <span class="text-[10px] px-1.5 py-0.5 rounded-full bg-[#EBF1ED] text-[#4A6B5D]">(${completedPlanTasks.length})</span>
                            </div>
                            ${completedPlanTasks.map((item, idx) => {
                                const isDone = true;
                                const isUnscheduled = !!item.isUnscheduled;
                                const isNow = false;
                                const isLast = idx === completedPlanTasks.length - 1;
                                return renderEmodeTimelineItem(item, isDone, isNow, isUnscheduled, isLast);
                            }).join('')}
                        ` : '';

                        return incompleteHTML + completedHTML;
                    })()}
                </div>
            </div>
            ${changeModePromptHTML}
        `;
    }

    // -------------------------------------------------------------------------
    // SHARED ECOSYSTEM FOR URGENT MODE (Excluded in favor of dedicated Urgent Support Row)
    // -------------------------------------------------------------------------
    function renderEmodeSharedEcosystem() {
        return '';
    }

    // -------------------------------------------------------------------------
    // DEDICATED URGENT SUPPORT ROW (Quick Relief + Focus now)
    // -------------------------------------------------------------------------
    function renderSupportRowHTML() {
        const titleQuickRelief = window.t ? window.t('modes.urgent.quickRelief', {}, (isViLocale() ? 'Thư giãn' : 'Quick Relief')) : (isViLocale() ? 'Thư giãn' : 'Quick Relief');
        const titleFocusNow = window.t ? window.t('modes.urgent.focusNow', {}, (isViLocale() ? 'Tập trung' : 'Focus Now')) : (isViLocale() ? 'Tập trung' : 'Focus Now');
        return `
            <div class="flex flex-col sm:flex-row items-center justify-center gap-4 sm:gap-5 w-full urgent-support-row" data-tempo-ui="urgent-support" style="margin-left: auto; margin-right: auto;">
                <!-- Tool 1: Quick Relief (Visually matched with latest EntryHome version) -->
                <div onclick="if (window.TempoStressRelief && window.TempoStressRelief.openModal) { window.TempoStressRelief.openModal(); } else if (window.TempoTriage && window.TempoTriage.openQuickReliefModal) { window.TempoTriage.openQuickReliefModal(); }"
                     role="button"
                     tabindex="0"
                     aria-label="${titleQuickRelief}"
                     onkeydown="if(event.key==='Enter'||event.key===' ') { event.preventDefault(); this.click(); }"
                     class="bg-[#DEECE5] border border-[#728F83]/30 rounded-3xl px-2.5 py-3.5 sm:px-2 sm:py-4 flex items-center justify-center shadow-xs hover:shadow-md transition cursor-pointer group relative overflow-visible urgent-card-overwhelmed shrink-0"
                     style="width: 334.92px; min-width: 334.92px; max-width: 334.92px; height: 100px; min-height: 100px; max-height: 100px; box-sizing: border-box; flex-shrink: 0;"
                     title="${titleQuickRelief}">
                    <div class="flex items-center justify-center gap-2 sm:gap-2.5" style="transform: translateX(10px);">
                        <div class="z-10 shrink-0">
                            <h3 class="text-[29px] sm:text-[31px] font-bold text-[#6D8A7E] leading-tight whitespace-nowrap">
                                ${titleQuickRelief}
                            </h3>
                        </div>
                        <img src="assets/quick-relief-mascot-transparent.png"
                             alt="${titleQuickRelief}"
                             class="h-[102px] w-auto object-contain shrink-0 select-none pointer-events-none group-hover:scale-105 transition-transform" />
                    </div>
                </div>

                <!-- Tool 2: Focus Now (Visually matched with latest EntryHome version) -->
                <div onclick="if (window.TempoFocusZone && window.TempoFocusZone.openQuickEntry) { window.TempoFocusZone.openQuickEntry(); } else if (window.TempoTriage && window.TempoTriage.launchFocusMode) { window.TempoTriage.launchFocusMode(); }"
                     role="button"
                     tabindex="0"
                     aria-label="${titleFocusNow}"
                     onkeydown="if(event.key==='Enter'||event.key===' ') { event.preventDefault(); this.click(); }"
                     class="bg-[#D29C85] border border-[#4A4541]/20 rounded-3xl px-2.5 py-3.5 sm:px-2 sm:py-4 flex items-center justify-center shadow-xs hover:shadow-md transition cursor-pointer group relative overflow-visible urgent-card-focus-now shrink-0"
                     style="width: 334.92px; min-width: 334.92px; max-width: 334.92px; height: 100px; min-height: 100px; max-height: 100px; box-sizing: border-box; flex-shrink: 0;"
                     title="${titleFocusNow}">
                    <div class="flex items-center justify-center gap-2 sm:gap-2.5" style="transform: translateX(-10px);">
                        <img src="assets/focus-now-mascot.png"
                             alt="${titleFocusNow}"
                             class="h-[102px] w-auto object-contain shrink-0 select-none pointer-events-none group-hover:scale-105 transition-transform" />
                        <div class="z-10 shrink-0">
                            <h3 class="text-[29px] sm:text-[31px] font-bold text-white leading-tight whitespace-nowrap">
                                ${titleFocusNow}
                            </h3>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }


    // -------------------------------------------------------------------------
    // LOWER SCROLL SECTION: Enjoy Tempo Tools + Từ Cộng đồng Tempo
    // -------------------------------------------------------------------------
    function renderLowerSelfCheckStreakCard() {
        const streakCount = (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.calculateStreak === 'function')
            ? window.TempoRecoverySelfCheck.calculateStreak()
            : 0;

        let rawActiveTrackers = (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.getActiveTrackers === 'function')
            ? window.TempoRecoverySelfCheck.getActiveTrackers()
            : [];

        const seenConcepts = new Set();
        const activeTrackers = [];
        rawActiveTrackers.forEach(trk => {
            if (!trk || !trk.name) return;
            const nameLower = trk.name.trim().toLowerCase();
            const conceptKey = nameLower.includes('tension') 
                ? 'stress_sign::tension' 
                : `${(trk.category || 'stress_sign').toLowerCase()}::${nameLower}`;
            if (!seenConcepts.has(conceptKey)) {
                seenConcepts.add(conceptKey);
                activeTrackers.push(trk);
            }
        });

        const answeredTrackers = activeTrackers.filter(t => typeof isRmodeTrackerAnsweredToday === 'function' && isRmodeTrackerAnsweredToday(t.id));
        const answeredCount = answeredTrackers.length;
        const totalCount = activeTrackers.length;
        const isConfigured = totalCount > 0;

        const skippedIds = new Set(getUmodeSkippedTrackers());
        const skippedTrackers = activeTrackers.filter(t => (typeof isRmodeTrackerAnsweredToday === 'function' && !isRmodeTrackerAnsweredToday(t.id)) && skippedIds.has(t.id));
        const pendingTrackers = activeTrackers.filter(t => (typeof isRmodeTrackerAnsweredToday === 'function' && !isRmodeTrackerAnsweredToday(t.id)) && !skippedIds.has(t.id));

        const displayTracker = pendingTrackers.length > 0 ? pendingTrackers[0] : null;

        let trackerMethod = 'percentage';
        if (displayTracker) {
            if (displayTracker.check_method) {
                trackerMethod = String(displayTracker.check_method).toLowerCase();
            } else if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.getTrackerConfigForDate === 'function') {
                const todayStr = (typeof getRmodeTodayDateStr === 'function') ? getRmodeTodayDateStr() : new Date().toISOString().slice(0, 10);
                const cfg = window.TempoRecoverySelfCheck.getTrackerConfigForDate(displayTracker, todayStr);
                if (cfg && cfg.check_method) {
                    trackerMethod = String(cfg.check_method).toLowerCase();
                }
            }
        }

        const trackerObs = (displayTracker && typeof getRmodeTodayObservation === 'function')
            ? getRmodeTodayObservation(displayTracker.id)
            : null;
        const isTrackerAnswered = trackerObs && trackerObs.status === 'answered' && trackerObs.value !== null && trackerObs.value !== undefined && trackerObs.value !== '';
        const trackerVal = isTrackerAnswered ? trackerObs.value : null;

        const trackerName = displayTracker ? displayTracker.name : 'Daily check-in';
        let dotColor = '#166545';
        if (displayTracker) {
            dotColor = displayTracker.type_color || (displayTracker.category === 'stress_sign' ? '#B84834' : (displayTracker.category === 'supportive' ? '#166545' : '#4A6B5D'));
        }

        const baseSummary = window.t ? window.t('modes.urgent.checkinSummary', { completed: answeredCount, total: totalCount }, (isViLocale() ? `Bạn đã check ${answeredCount}/${totalCount} mục hôm nay.` : `You checked in on ${answeredCount} of ${totalCount} things.`)) : (isViLocale() ? `Bạn đã check ${answeredCount}/${totalCount} mục hôm nay.` : `You checked in on ${answeredCount} of ${totalCount} things.`);
        const skippedExtra = skippedTrackers.length > 0 ? (isViLocale() ? ` (${skippedTrackers.length} đã bỏ qua)` : ` (${skippedTrackers.length} skipped)`) : '';
        let summaryText = baseSummary + skippedExtra;
        let btn1Text = window.t ? window.t('modes.urgent.viewTodayCheckin', {}, (isViLocale() ? 'Xem check-in hôm nay' : "View today's checkin")) : (isViLocale() ? 'Xem check-in hôm nay' : "View today's checkin");
        let btn1Action = "if (window.TempoMode && typeof window.TempoMode.handleStreakCardCheckin === 'function') { window.TempoMode.handleStreakCardCheckin(); } else if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.openDailyCheckin === 'function') { window.TempoRecoverySelfCheck.openDailyCheckin(false); } else { window.location.hash = '#stress-check'; }";
        let btn2Text = window.t ? window.t('modes.urgent.editTrackingSystem', {}, (isViLocale() ? 'Sửa tracking' : 'Edit tracking system')) : (isViLocale() ? 'Sửa tracking' : 'Edit tracking system');
        const skipBtnText = window.t ? window.t('modes.urgent.skip', {}, (isViLocale() ? 'Bỏ qua' : 'Skip')) : (isViLocale() ? 'Bỏ qua' : 'Skip');
        const saveBtnText = window.t ? window.t('modes.urgent.save', {}, (isViLocale() ? 'Lưu' : 'Save')) : (isViLocale() ? 'Lưu' : 'Save');
        const streakHeadingText = window.t ? window.t('modes.urgent.streakHeading', {}, (isViLocale() ? 'Chuỗi Self-check 🔥' : 'Your Self-check Streak 🔥')) : (isViLocale() ? 'Chuỗi Self-check 🔥' : 'Your Self-check Streak 🔥');
        let btn2Action = "if (window.TempoMode && typeof window.TempoMode.openStrack === 'function') { window.TempoMode.openStrack('open', { sourceContext: 'emergency' }); } else if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') { window.TempoApp.navigateTo('stress-check'); } else { window.location.hash = '#stress-check'; }";

        let middleControlHtml = '';

        if (!isConfigured) {
            dotColor = '#9AAFA1';
            summaryText = 'No tracking items set up yet.';
            btn1Text = 'Set up check-in';
            btn1Action = "if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.openSetup === 'function') { window.TempoRecoverySelfCheck.openSetup(); } else if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') { window.TempoApp.navigateTo('stress-check'); } else { window.location.hash = '#stress-check'; }";
            btn2Text = 'Add tracking';
            btn2Action = "if (window.TempoMode && typeof window.TempoMode.openStrack === 'function') { window.TempoMode.openStrack('add', { sourceContext: 'emergency' }); } else if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') { window.TempoApp.navigateTo('stress-check'); } else { window.location.hash = '#stress-check'; }";

            middleControlHtml = `
                <div class="space-y-2 py-0.5">
                    <div class="flex items-center space-x-2 shrink-0">
                        <span class="w-2.5 h-2.5 rounded-full inline-block shrink-0 bg-[#9AAFA1]"></span>
                        <span class="font-bold text-sm sm:text-base text-[#484541]">No trackers configured</span>
                    </div>
                    <p class="text-xs text-[#7B7672] font-medium" data-tempo-ui="streak-card-summary">
                        ${escapeHtml(summaryText)}
                    </p>
                </div>
            `;
        } else if (pendingTrackers.length === 0) {
            // All items processed (answered or skipped)
            const allChecked = answeredCount === totalCount;
            middleControlHtml = `
                <div class="space-y-2.5 py-1" data-tempo-ui="streak-card-completion-summary">
                    <div class="flex items-center space-x-2.5 text-sm sm:text-base font-bold ${allChecked ? 'text-[#166545]' : 'text-[#484541]'}">
                        <span class="w-3 h-3 rounded-full ${allChecked ? 'bg-[#166545]' : 'bg-[#7B9688]'} inline-block shrink-0"></span>
                        <span>${allChecked ? 'All check-ins completed today! 🎉' : 'Today’s check-in complete'}</span>
                    </div>
                    <div class="flex items-center justify-between text-xs sm:text-[13px] text-[#5B5550] pt-0.5">
                        <span data-tempo-ui="streak-card-summary">${baseSummary}</span>
                        ${skippedTrackers.length > 0 ? `
                            <button type="button" 
                                    onclick="window.TempoMode.resetUmodeSkippedTrackers()"
                                    class="text-xs font-bold text-[#4A6B5D] hover:underline cursor-pointer"
                                    data-tempo-ui="streak-card-review-skipped-btn">
                                Review ${skippedTrackers.length} skipped
                            </button>
                        ` : ''}
                    </div>
                </div>
            `;
        } else if (trackerMethod === 'scale') {
            const scaleMin = displayTracker.scale_min !== undefined ? Number(displayTracker.scale_min) : 1;
            const scaleMax = displayTracker.scale_max !== undefined ? Number(displayTracker.scale_max) : (displayTracker.scale_range === '1-10' ? 10 : 5);
            const scaleMinLabel = displayTracker.scale_min_label || 'Low';
            const scaleMaxLabel = displayTracker.scale_max_label || 'High';

            const scaleButtonsHtml = [];
            for (let n = scaleMin; n <= scaleMax; n++) {
                const isSelected = isTrackerAnswered && Number(trackerVal) === n;
                scaleButtonsHtml.push(`
                    <button type="button"
                            onclick="window.TempoMode.submitUmodeSelfCheckValue('${displayTracker.id}', ${n})"
                            class="w-8 h-8 sm:w-9 sm:h-9 rounded-xl text-xs sm:text-sm font-bold transition cursor-pointer border flex items-center justify-center shadow-2xs select-none ${isSelected ? 'bg-[#166545] text-white border-[#166545] shadow-xs ring-2 ring-[#166545]/20' : 'bg-white text-[#37352F] border-stone-300/80 hover:border-[#166545] hover:bg-[#F4F7F5]'}"
                            data-scale-val="${n}"
                            aria-pressed="${isSelected}">
                        ${n}
                    </button>
                `);
            }

            middleControlHtml = `
                <div class="space-y-2 py-0.5" data-tempo-ui="streak-card-scale-control">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-2 shrink-0">
                            <span class="w-2.5 h-2.5 rounded-full inline-block shrink-0" style="background-color: ${dotColor};"></span>
                            <span class="font-bold text-sm sm:text-base text-[#484541]">${escapeHtml(trackerName)}</span>
                        </div>
                        <button type="button"
                                onclick="window.TempoMode.skipUmodeCurrentSelfCheck('${displayTracker.id}')"
                                class="text-xs font-semibold text-[#8C8681] hover:text-[#37352F] hover:bg-stone-200/50 px-2.5 py-1 rounded-lg transition cursor-pointer shrink-0"
                                title="Skip for now"
                                data-tempo-ui="streak-card-skip-btn">
                            ${skipBtnText}
                        </button>
                    </div>
                    <div class="flex flex-col space-y-1">
                        <div class="flex items-center space-x-1.5 overflow-x-auto pb-0.5" role="group" aria-label="${escapeHtml(trackerName)} scale">
                            ${scaleButtonsHtml.join('')}
                        </div>
                        <div class="flex justify-between text-[10px] sm:text-[11px] text-[#8C766E] font-medium px-0.5 max-w-[210px]">
                            <span>${escapeHtml(scaleMinLabel)}</span>
                            <span>${escapeHtml(scaleMaxLabel)}</span>
                        </div>
                    </div>
                    <p class="text-xs text-[#7B7672] font-medium" data-tempo-ui="streak-card-summary">
                        ${escapeHtml(summaryText)}
                    </p>
                </div>
            `;
        } else if (trackerMethod === 'options' || trackerMethod === 'yes_no') {
            let opts = displayTracker.options;
            if (!opts || !Array.isArray(opts) || opts.length === 0) {
                opts = ['Yes', 'No'];
            }
            const optButtons = opts.map(opt => {
                const isSelected = isTrackerAnswered && String(trackerVal).toLowerCase() === String(opt).toLowerCase();
                return `
                    <button type="button"
                            onclick="window.TempoMode.submitUmodeSelfCheckValue('${displayTracker.id}', '${escapeHtml(opt)}')"
                            class="px-3.5 py-1.5 rounded-xl text-xs font-bold transition cursor-pointer border shadow-2xs select-none ${isSelected ? 'bg-[#166545] text-white border-[#166545]' : 'bg-white text-[#37352F] border-stone-300/80 hover:border-[#166545] hover:bg-[#F4F7F5]'}">
                        ${escapeHtml(opt)}
                    </button>
                `;
            }).join('');

            middleControlHtml = `
                <div class="space-y-2 py-0.5" data-tempo-ui="streak-card-options-control">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-2 shrink-0">
                            <span class="w-2.5 h-2.5 rounded-full inline-block shrink-0" style="background-color: ${dotColor};"></span>
                            <span class="font-bold text-sm sm:text-base text-[#484541]">${escapeHtml(trackerName)}</span>
                        </div>
                        <button type="button"
                                onclick="window.TempoMode.skipUmodeCurrentSelfCheck('${displayTracker.id}')"
                                class="text-xs font-semibold text-[#8C8681] hover:text-[#37352F] hover:bg-stone-200/50 px-2.5 py-1 rounded-lg transition cursor-pointer shrink-0"
                                title="Skip for now"
                                data-tempo-ui="streak-card-skip-btn">
                            ${skipBtnText}
                        </button>
                    </div>
                    <div class="flex items-center space-x-1.5 pt-0.5">
                        ${optButtons}
                    </div>
                    <p class="text-xs text-[#7B7672] font-medium" data-tempo-ui="streak-card-summary">
                        ${escapeHtml(summaryText)}
                    </p>
                </div>
            `;
        } else if (trackerMethod === 'quantity') {
            const unit = displayTracker.quantity_unit || 'min';
            middleControlHtml = `
                <div class="space-y-2 py-0.5" data-tempo-ui="streak-card-quantity-control">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-2 shrink-0">
                            <span class="w-2.5 h-2.5 rounded-full inline-block shrink-0" style="background-color: ${dotColor};"></span>
                            <span class="font-bold text-sm sm:text-base text-[#484541]">${escapeHtml(trackerName)}</span>
                        </div>
                        <button type="button"
                                onclick="window.TempoMode.skipUmodeCurrentSelfCheck('${displayTracker.id}')"
                                class="text-xs font-semibold text-[#8C8681] hover:text-[#37352F] hover:bg-stone-200/50 px-2.5 py-1 rounded-lg transition cursor-pointer shrink-0"
                                title="Skip for now"
                                data-tempo-ui="streak-card-skip-btn">
                            ${skipBtnText}
                        </button>
                    </div>
                    <div class="flex items-center flex-wrap gap-2 pt-0.5">
                        <input type="number" 
                               id="umode-qty-input-${displayTracker.id}"
                               placeholder="Enter quantity"
                               min="0"
                               step="any"
                               class="w-28 sm:w-32 px-3 py-1.5 text-xs font-semibold rounded-xl border border-stone-300 focus:outline-none focus:border-[#4A6B5D] bg-white shadow-2xs">
                        <span class="text-xs font-bold text-[#5B5550]">${escapeHtml(unit)}</span>
                        <button type="button" 
                                onclick="window.TempoMode.confirmUmodeQuantity('${displayTracker.id}')"
                                class="px-3.5 py-1.5 rounded-xl text-xs font-bold bg-[#859B8B] hover:bg-[#758B7B] text-white transition cursor-pointer shrink-0 shadow-2xs">
                            ${saveBtnText}
                        </button>
                        <button type="button" 
                                onclick="window.TempoMode.submitUmodeSelfCheckValue('${displayTracker.id}', 'no')"
                                class="px-2.5 py-1.5 rounded-xl text-xs font-semibold text-stone-500 hover:text-stone-700 hover:bg-stone-100 transition cursor-pointer">
                            Didn't do
                        </button>
                    </div>
                    <p class="text-xs text-[#7B7672] font-medium" data-tempo-ui="streak-card-summary">
                        ${escapeHtml(summaryText)}
                    </p>
                </div>
            `;
        } else {
            // Default / percentage: genuinely interactive draggable slider
            let percentVal = 50;
            if (trackerVal !== null && trackerVal !== undefined && !isNaN(Number(trackerVal))) {
                percentVal = Math.max(0, Math.min(100, Math.round(Number(trackerVal))));
            }

            middleControlHtml = `
                <div class="space-y-2 py-0.5" data-tempo-ui="streak-card-percentage-control">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-2 shrink-0">
                            <span class="w-2.5 h-2.5 rounded-full inline-block shrink-0" style="background-color: ${dotColor};"></span>
                            <span class="font-bold text-sm sm:text-base text-[#484541]">${escapeHtml(trackerName)}</span>
                        </div>
                        <button type="button"
                                onclick="window.TempoMode.skipUmodeCurrentSelfCheck('${displayTracker.id}')"
                                class="text-xs font-semibold text-[#8C8681] hover:text-[#37352F] hover:bg-stone-200/50 px-2.5 py-1 rounded-lg transition cursor-pointer shrink-0"
                                title="Skip for now"
                                data-tempo-ui="streak-card-skip-btn">
                            ${skipBtnText}
                        </button>
                    </div>
                    <div class="flex items-center space-x-3 pt-0.5">
                        <div class="relative flex-1 min-w-0 pt-1 pb-4 select-none cursor-pointer"
                             id="umode-slider-track-container"
                             data-tracker-id="${displayTracker.id}"
                             onpointerdown="window.TempoMode.handleUmodeTrackPointer(event, '${displayTracker.id}')"
                             onpointermove="if (event.buttons === 1) window.TempoMode.handleUmodeTrackPointer(event, '${displayTracker.id}')"
                             onpointerup="window.TempoMode.handleUmodeTrackPointer(event, '${displayTracker.id}')"
                             style="touch-action: none;">
                            <div class="w-full h-2 bg-[#FDE8DF] rounded-full overflow-hidden">
                                <div id="umode-slider-fill" class="h-full bg-[#E08A6C] rounded-full" style="width: ${percentVal}%;"></div>
                            </div>
                            <div id="umode-slider-thumb" class="absolute top-0 flex flex-col items-center pointer-events-none" style="left: ${percentVal}%; transform: translateX(-50%);">
                                <div class="w-4 h-4 rounded-full ring-2 ring-white shadow-xs cursor-pointer" style="background-color: ${dotColor};"></div>
                                <span id="umode-slider-badge" class="text-[10px] sm:text-[11px] font-bold text-[#8C766E] mt-0.5 select-none">${percentVal}%</span>
                            </div>
                            <input type="range" 
                                   min="0" 
                                   max="100" 
                                   value="${percentVal}" 
                                   id="umode-selfcheck-range"
                                   data-tracker-id="${displayTracker.id}"
                                   aria-label="${escapeHtml(trackerName)} percentage"
                                   aria-valuenow="${percentVal}"
                                   aria-valuemin="0"
                                   aria-valuemax="100"
                                   oninput="window.TempoMode.handleUmodeSliderInput(this, '${displayTracker.id}')"
                                   onchange="window.TempoMode.handleUmodeSliderChange(this, '${displayTracker.id}')"
                                   class="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10" 
                                   style="margin: 0; padding: 0;">
                        </div>
                        <button type="button" 
                                id="btn-umode-save-percentage"
                                onclick="window.TempoMode.confirmUmodePercentage('${displayTracker.id}')"
                                class="px-3.5 py-1.5 rounded-xl text-xs font-bold bg-[#859B8B] hover:bg-[#758B7B] text-white shadow-2xs transition cursor-pointer shrink-0">
                            ${saveBtnText}
                        </button>
                    </div>
                    <p class="text-xs text-[#7B7672] font-medium" data-tempo-ui="streak-card-summary">
                        ${escapeHtml(summaryText)}
                    </p>
                </div>
            `;
        }

        return `
            <div class="self-end shrink-0 w-full lg:w-[678.5px] lg:max-w-none min-h-[264px] lg:h-[264px] bg-[#FEFAF4] border border-[#EAE4DF] rounded-3xl p-5 sm:p-6 soft-card-shadow flex flex-col justify-between space-y-4" data-tempo-ui="lower-selfcheck-streak" style="min-height: 264px;">
                <!-- Header: Heading & Flame Badge -->
                <div class="flex items-center space-x-3">
                    <h3 class="text-xl sm:text-[23px] font-extrabold text-[#375344] tracking-tight leading-tight">
                        ${streakHeadingText}
                    </h3>
                    <!-- Flame/Streak Badge Container: Custom flame asset with native aspect ratio preserved -->
                    <div class="relative inline-flex items-center justify-center shrink-0 w-8 h-8 sm:w-9 sm:h-9" data-tempo-ui="streak-flame-container" title="${streakCount}-day streak">
                        <div class="w-full h-full flex items-center justify-center select-none" data-tempo-ui="streak-flame-asset">
                            <img src="assets/custom_flame.png" alt="Streak flame" class="w-full h-full max-w-full max-h-full object-contain select-none pointer-events-none drop-shadow-xs">
                        </div>
                        <span class="absolute text-[11px] sm:text-xs font-black text-white pointer-events-none select-none" style="transform: translate(0px, 2px); text-shadow: 0 1px 2px rgba(0,0,0,0.6);">${streakCount}</span>
                    </div>
                </div>

                <!-- Tracker Item & Dynamic Tracking Control -->
                ${middleControlHtml}

                <!-- Action Buttons -->
                <div class="pt-0.5 flex items-center space-x-3 flex-wrap gap-y-2">
                    <button type="button" 
                            data-tempo-ui="streak-card-btn1"
                            onclick="${btn1Action}"
                            class="px-5 py-2.5 rounded-xl font-bold text-xs sm:text-sm bg-[#859B8B] hover:bg-[#758B7B] text-white shadow-xs transition cursor-pointer">
                        ${escapeHtml(btn1Text)}
                    </button>
                    <button type="button" 
                            data-tempo-ui="streak-card-btn2"
                            onclick="${btn2Action}"
                            class="px-5 py-2.5 rounded-xl font-bold text-xs sm:text-sm bg-white border border-[#9AAFA1] text-[#4E5E54] hover:bg-[#F4F7F5] shadow-xs transition cursor-pointer">
                        ${escapeHtml(btn2Text)}
                    </button>
                </div>
            </div>
        `;
    }

    function syncUmodeCreateNotesAlignment() {
        const streakCard = document.querySelector('[data-tempo-ui="lower-selfcheck-streak"]');
        const notesCard = document.querySelector('#urgent-rebuilt-section [data-tempo-ui="lower-create-notes"]');
        if (!streakCard || !notesCard) return;
        if (window.innerWidth >= 1024) {
            notesCard.style.width = '510px';
            notesCard.style.height = '122px';
            notesCard.style.marginLeft = '-44.25px';
            notesCard.style.marginRight = '0px';
            const streakRect = streakCard.getBoundingClientRect();
            const notesRect = notesCard.getBoundingClientRect();
            const streakCenter = streakRect.left + streakRect.width / 2;
            const notesCenter = notesRect.left + notesRect.width / 2;
            const diff = streakCenter - notesCenter;
            if (Math.abs(diff) > 0.1) {
                const currentMl = parseFloat(notesCard.style.marginLeft) || -44.25;
                notesCard.style.marginLeft = (currentMl + diff) + 'px';
            }
        } else {
            notesCard.style.width = 'calc(100% - 40px)';
            notesCard.style.height = '122px';
            notesCard.style.marginLeft = 'auto';
            notesCard.style.marginRight = 'auto';
        }
    }

    function formatNoteTime(note) {
        if (!note) return '';
        if (note.time) return note.time;
        const iso = note.createdAt || note.updatedAt;
        if (iso) {
            try {
                const d = new Date(iso);
                if (!isNaN(d.getTime())) {
                    let hours = d.getHours();
                    const minutes = String(d.getMinutes()).padStart(2, '0');
                    const ampm = hours >= 12 ? 'PM' : 'AM';
                    hours = hours % 12;
                    hours = hours ? hours : 12;
                    return `${hours}:${minutes} ${ampm}`;
                }
            } catch (e) {}
        }
        return '';
    }

    function getUmodeDayNotesForToday(targetDate) {
        const today = targetDate || (typeof getTodayISOString === 'function' ? getTodayISOString() : new Date().toISOString().slice(0, 10));
        const allNotes = [];
        const seenIds = new Set();

        function addCandidate(n) {
            if (!n) return;
            // Strictly exclude task notes
            if (n.taskId || n.category === 'task' || n.type === 'task') return;
            // Must be day note or general note without task association
            const isDay = n.category === 'day' || n.type === 'day' || (!n.taskId && n.category !== 'task' && n.type !== 'task');
            if (!isDay) return;

            // Check date match strictly against targetDate
            let nDate = '';
            if (n.date && typeof n.date === 'string') {
                nDate = n.date.slice(0, 10);
            } else if (n.createdAt && typeof n.createdAt === 'string') {
                nDate = n.createdAt.slice(0, 10);
            } else if (n.updatedAt && typeof n.updatedAt === 'string') {
                nDate = n.updatedAt.slice(0, 10);
            }
            if (nDate !== today) return;

            const noteId = String(n.id || (n.text ? n.text.slice(0, 30) : Math.random()));
            if (!seenIds.has(noteId)) {
                seenIds.add(noteId);
                allNotes.push(n);
            }
        }

        // 1. First source: window.TempoToolNotes.getDayNotes(today)
        if (typeof window !== 'undefined' && window.TempoToolNotes && typeof window.TempoToolNotes.getDayNotes === 'function') {
            try {
                const tnNotes = window.TempoToolNotes.getDayNotes(today) || [];
                if (Array.isArray(tnNotes)) {
                    tnNotes.forEach(addCandidate);
                }
            } catch (e) {}
        }

        // 2. Second source: localStorage keys
        try {
            let uid = 'local_user';
            if (typeof window !== 'undefined' && window.TempoAuth && typeof window.TempoAuth.getCurrentUserId === 'function') {
                const u = window.TempoAuth.getCurrentUserId();
                if (u) uid = u;
            } else if (typeof window !== 'undefined' && window.TempoAuth && typeof window.TempoAuth.getUser === 'function') {
                const u = window.TempoAuth.getUser();
                if (u && u.id) uid = u.id;
            }

            const keysToCheck = [
                `tempo_day_notes_${uid}`,
                'tempo_day_notes',
                `tempo_tool_notes_${uid}`,
                'tempo_tool_notes'
            ];

            for (const k of keysToCheck) {
                const raw = localStorage.getItem(k);
                if (!raw) continue;
                try {
                    const parsed = JSON.parse(raw);
                    if (Array.isArray(parsed)) {
                        parsed.forEach(addCandidate);
                    }
                } catch (err) {}
            }
        } catch (e) {}

        // Sort latest first
        allNotes.sort((a, b) => {
            const timeA = new Date(a.createdAt || a.updatedAt || a.date || 0).getTime();
            const timeB = new Date(b.createdAt || b.updatedAt || b.date || 0).getTime();
            return timeB - timeA;
        });

        return allNotes;
    }

    function renderEmodeCreateNotesCard(ctx) {
        const todayStr = (ctx && ctx.todayStr) || (typeof getTodayISOString === 'function' ? getTodayISOString() : new Date().toISOString().slice(0, 10));
        const dayNotes = getUmodeDayNotesForToday(todayStr);
        const isVi = typeof isViLocale === 'function' ? isViLocale() : (window.TempoI18n?.getCurrentLanguage?.() === 'vi');
        const createNoteForTodayLabel = window.t ? window.t('modes.urgent.createNoteForToday', {}, (isVi ? 'Tạo ghi chú cho hôm nay' : 'Create a note for today')) : (isVi ? 'Tạo ghi chú cho hôm nay' : 'Create a note for today');
        const createNotesTitleLabel = window.t ? window.t('modes.urgent.createNotes', {}, (isVi ? 'Tạo Notes' : 'Create Notes')) : (isVi ? 'Tạo Notes' : 'Create Notes');
        const viewMyNotesLabel = window.t ? window.t('modes.urgent.viewMyNotes', {}, (isVi ? 'Xem ghi chú' : 'View my notes')) : (isVi ? 'Xem ghi chú' : 'View my notes');

        let notesListHTML = '';
        if (!dayNotes || dayNotes.length === 0) {
            notesListHTML = `
                <div data-no-card-click="true"
                     onclick="event.stopPropagation(); if (window.TempoToolNotes && typeof window.TempoToolNotes.openCreateNoteModal === 'function') { window.TempoToolNotes.openCreateNoteModal('day'); }"
                     class="h-full min-h-[78px] flex flex-col items-center justify-center text-center px-3 py-2 bg-[#FCF5F0]/70 hover:bg-[#F6E3DA] border border-dashed border-[#E8D5CA] hover:border-[#D79277] rounded-2xl transition cursor-pointer select-none group" 
                     data-tempo-ui="notes-empty-state"
                     title="${escapeHTML(createNoteForTodayLabel)}">
                    <span class="text-base text-[#B87561] mb-0.5 group-hover:scale-110 transition-transform">📝</span>
                    <p class="text-xs font-semibold text-[#8C7D75] group-hover:text-[#554741] transition-colors">${escapeHTML(createNoteForTodayLabel)}</p>
                </div>
            `;
        } else {
            notesListHTML = `
                <div class="overflow-y-auto max-h-[96px] space-y-1.5 pr-1 text-left custom-scrollbar" data-tempo-ui="notes-scroll-list" style="max-height: 96px; overflow-y: auto;">
                    ${dayNotes.map(n => {
                        const noteText = escapeHTML(n.text || n.content || n.note || '');
                        const timeStr = formatNoteTime(n);
                        const safeId = escapeHTML(String(n.id || ''));
                        return `
                            <div data-no-card-click="true"
                                 onclick="event.stopPropagation(); if (window.TempoToolNotes && typeof window.TempoToolNotes.openNoteDetailModal === 'function') { window.TempoToolNotes.openNoteDetailModal('${safeId}'); } else if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') { window.TempoApp.navigateTo('notes'); }"
                                 class="bg-white/90 hover:bg-white border border-[#EBDCD3] hover:border-[#D9C4B7] rounded-xl px-2.5 py-1.5 transition text-xs shadow-2xs group cursor-pointer" 
                                 data-day-note-id="${safeId}"
                                 title="Click to view full note details">
                                <div class="flex items-center justify-between gap-1 mb-0.5 pointer-events-none">
                                    <span class="text-[10px] font-bold uppercase tracking-wider text-[#B87561] flex items-center gap-1">
                                        <span>📝</span>
                                        <span>Day Note</span>
                                    </span>
                                    ${timeStr ? `<span class="text-[10px] text-[#9E9087] font-medium">${escapeHTML(timeStr)}</span>` : ''}
                                </div>
                                <p class="text-[11.5px] text-[#484541] font-medium leading-snug line-clamp-2 break-words pointer-events-none">
                                    ${noteText}
                                </p>
                            </div>
                        `;
                    }).join('')}
                </div>
            `;
        }

        return `
            <div class="w-full min-h-[122px] max-h-[122px] h-[122px] bg-[#F9E8E2] border border-[#E8D5CA] rounded-3xl p-3.5 sm:p-4 shadow-xs flex flex-row items-center justify-between box-border relative overflow-hidden cursor-pointer" 
                 data-tempo-ui="urmode-create-notes" 
                 onclick="if (event.target.closest('[data-no-card-click]')) return; if (window.TempoToolNotes && typeof window.TempoToolNotes.openCreateNoteModal === 'function') { window.TempoToolNotes.openCreateNoteModal('day'); }"
                 title="Click to create a note"
                 style="width: 100%; height: 122px; min-height: 122px; max-height: 122px; box-sizing: border-box; overflow: hidden;">
                <!-- Left: Title & View Button -->
                <div class="flex flex-col justify-between shrink-0 space-y-2 pr-3 sm:pr-4 border-r border-[#E8D5CA]/70" data-tempo-ui="notes-text-block" style="min-width: 120px; max-width: 135px;">
                    <h3 class="text-lg sm:text-xl font-bold text-[#554741] leading-tight tracking-tight">
                        ${escapeHTML(createNotesTitleLabel)}
                    </h3>
                    <div>
                        <button type="button"
                                data-no-card-click="true"
                                onclick="event.stopPropagation(); if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') { window.TempoApp.navigateTo('notes'); } else { window.location.hash = '#notes'; }"
                                class="px-3 py-1.5 rounded-xl font-bold text-xs bg-[#C88E7D] hover:bg-[#B97F6E] text-white shadow-2xs transition cursor-pointer inline-flex items-center justify-center whitespace-nowrap">
                            ${escapeHTML(viewMyNotesLabel)}
                        </button>
                    </div>
                </div>

                <!-- Right: Today's Day Notes List (Scrollable) -->
                <div class="flex-1 min-w-0 pl-3 sm:pl-4 h-full flex flex-col justify-center" data-tempo-ui="notes-list-container">
                    ${notesListHTML}
                </div>
            </div>
        `;
    }

    function refreshNotesCardIfPresent() {
        const cardEls = document.querySelectorAll('[data-tempo-ui="urmode-create-notes"]');
        if (!cardEls || cardEls.length === 0) return;
        cardEls.forEach(cardEl => {
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = renderEmodeCreateNotesCard().trim();
            const newCard = tempDiv.firstElementChild;
            if (newCard) {
                cardEl.replaceWith(newCard);
            }
        });
    }

    function renderLowerCreateNotesCard() {
        return renderEmodeCreateNotesCard();
    }

    // -------------------------------------------------------------------------
    // LOWER SCROLL SECTION: Reconstructed Two-Column Dashboard Section
    // -------------------------------------------------------------------------
    function renderEmodeLowerSection() {
        return `
            <div id="urgent-rebuilt-section" class="pt-8 border-t border-[#D0E0D7] mt-8 w-full" data-tempo-ui="urgent-lower-section">
                <div class="max-w-[960px] mx-auto w-full grid grid-cols-1 lg:grid-cols-12 gap-5 lg:gap-6 items-start lg:translate-x-[59.25px]" data-tempo-ui="urgent-lower-grid">
                    
                    <!-- LEFT COLUMN (approx 58%): Self-check Streak -->
                    <div class="lg:col-span-7 flex flex-col space-y-4 w-full">
                        ${renderLowerSelfCheckStreakCard()}
                    </div>

                    <!-- RIGHT COLUMN (approx 42%): Từ Cộng đồng Tempo Panel -->
                    <div class="lg:col-span-5 w-full flex flex-col items-center">
                        ${renderTempoPostsSection()}
                    </div>

                </div>
                <style>
                    @media (min-width: 1024px) {
                        [data-tempo-ui="urgent-lower-grid"] {
                            transform: translateX(59.25px);
                        }
                    }
                </style>
            </div>
        `;
    }

    // -------------------------------------------------------------------------
    // -------------------------------------------------------------------------
    // TEMPO POSTS COMPONENT (Lightweight Community Social Feed Previews)
    // Visual design matches EntryHome Từ Cộng đồng Tempo preview exactly
    // -------------------------------------------------------------------------
    function renderTempoPostsSection() {
        let allPosts = (window.TempoCommunity && typeof window.TempoCommunity.getAllPosts === 'function')
            ? window.TempoCommunity.getAllPosts()
            : [];
        if (!Array.isArray(allPosts) || allPosts.length === 0) {
            if (window.TempoCommunity && typeof window.TempoCommunity.getInitialPosts === 'function') {
                allPosts = window.TempoCommunity.getInitialPosts();
            }
        }
        const distinctPosts = (window.TempoCommunity && typeof window.TempoCommunity.getDistinctPosts === 'function')
            ? window.TempoCommunity.getDistinctPosts(allPosts, 2)
            : (Array.isArray(allPosts) ? allPosts.slice(0, 2) : []);

        let postsCardsHTML = '';
        if (distinctPosts.length > 0) {
            if (window.TempoCommunity && typeof window.TempoCommunity.renderPreviewPostCardHTML === 'function') {
                postsCardsHTML = distinctPosts.map(p => window.TempoCommunity.renderPreviewPostCardHTML(p)).join('');
            } else if (typeof renderCommunityPreviewsHTML === 'function') {
                postsCardsHTML = renderCommunityPreviewsHTML(distinctPosts);
            }
        } else {
            postsCardsHTML = `
                <div class="h-48 flex flex-col items-center justify-center text-center p-6 space-y-2 text-[#8E8A85]">
                    <img src="assets/comment_action_symbol.png" alt="No posts" class="w-6 h-6 opacity-40 object-contain mb-0.5">
                    <p class="text-xs font-bold text-[#5A5550]">No community posts yet</p>
                    <p class="text-[10.5px] text-[#8E8A85] leading-relaxed">Be the first to share with your peers in the community.</p>
                </div>
            `;
        }

        return `
            <div class="urgent-section-posts bg-[#FEFAF4] border border-[#EAE4DF] rounded-3xl sm:rounded-[32px] p-4.5 sm:p-5 shadow-xs flex flex-col justify-between space-y-3.5 box-border" 
                 data-tempo-ui="urgent-posts"
                 style="width: calc(100% + 20px); margin-left: -10px; margin-right: -10px; box-sizing: border-box;">
                <!-- Header -->
                <div class="flex items-center justify-between pb-0.5 w-full">
                    <div class="flex items-center space-x-2.5">
                        <div class="w-8 h-8 rounded-full bg-[#F6E6DE] flex items-center justify-center shrink-0">
                            <img src="assets/comment_action_symbol.png" alt="Community" class="w-4 h-4 object-contain" />
                        </div>
                        <h3 class="font-bold text-base sm:text-lg text-[#55504C] tracking-tight">
                            ${window.t ? window.t('modes.urgent.fromCommunity', {}, (isViLocale() ? 'Cộng đồng Tempo' : 'From the Tempo Community')) : (isViLocale() ? 'Cộng đồng Tempo' : 'From the Tempo Community')}
                        </h3>
                    </div>
                    <button type="button" 
                            id="btn-see-all-posts-urgent"
                            onclick="if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') { window.TempoApp.navigateTo('community'); } else { window.location.hash = '#community?tab=posts'; } if (window.TempoCommunity && typeof window.TempoCommunity.selectTab === 'function') { window.TempoCommunity.selectTab('posts'); }" 
                            class="px-3.5 py-1 rounded-full bg-[#FCEFE8] hover:bg-[#F8E1D5] text-[#DE8662] text-xs font-bold transition flex items-center space-x-1 cursor-pointer"
                            aria-label="${isViLocale() ? 'Xem tất cả →' : 'View all →'}" title="${isViLocale() ? 'Xem tất cả →' : 'View all →'}">
                        <span>${(window.t ? (window.t('modes.urgent.viewAll') || window.t('modes.urgent.seeAll')) : null) || (isViLocale() ? 'Xem tất cả' : 'View all')}</span>
                        <span class="text-xs">&rarr;</span>
                    </button>
                </div>

                <!-- Posts list -->
                <div id="urgent-community-posts-list" class="space-y-3 flex-1 flex flex-col justify-between w-full">
                    ${postsCardsHTML}
                </div>
            </div>
        `;
    }

    // Preserved for backwards compatibility
    function renderQuickToolsSection(modeContext = 'active') {
        return renderSupportRowHTML();
    }

    // =========================================================================
    // RECOVERY MODE HOME (RMODE) IMPLEMENTATION (PHASE 1)
    // =========================================================================

    let selfCheckConfigState = null;
    let recentlyConfigState = null;
    let weeklyReviewDismissed = false;
    let weeklyReviewOverrideReady = false;

    function getSelfCheckState() {
        if (selfCheckConfigState) return selfCheckConfigState;
        try {
            if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.getState === 'function') {
                return window.TempoRecoverySelfCheck.getState();
            }
            const saved = localStorage.getItem('tempo_recovery_selfcheck_config');
            if (saved) {
                return JSON.parse(saved);
            }
        } catch (e) {}
        return { type: 'STATE_A' }; // Default honest empty for Phase 1
    }

    function setSelfCheckState(state) {
        selfCheckConfigState = state;
        try {
            localStorage.setItem('tempo_recovery_selfcheck_config', JSON.stringify(state));
        } catch (e) {}
        if (activeContext === MODES.RECOVERY) renderRmodeHome();
    }

    function handleRecoveryIntroSetupClick() {
        if (window.TempoRecoverySetup) {
            if (typeof window.TempoRecoverySetup.handleRmodeEntry === 'function') {
                window.TempoRecoverySetup.handleRmodeEntry({ force: true });
            } else if (typeof window.TempoRecoverySetup.open === 'function') {
                window.TempoRecoverySetup.open(1, { force: true });
            }
        } else if (typeof openStrack === 'function') {
            openStrack('setup', { stage: 1 });
        }
    }

    function handleAddTrackingDirectClick() {
        openStrack('open', { sourceContext: 'recovery', openAdjust: true });
    }

    function handleSelfCheckSetupClick() {
        handleRecoveryIntroSetupClick();
    }

    function handleSelfCheckAction(action) {
        openStrack(action);
    }

    function handleStreakCardCheckin() {
        if (window.TempoRecoverySelfCheck) {
            let active = (typeof window.TempoRecoverySelfCheck.getActiveTrackers === 'function')
                ? window.TempoRecoverySelfCheck.getActiveTrackers()
                : [];

            if (active.length === 0) {
                if (typeof window.TempoRecoverySelfCheck.openSetup === 'function') {
                    window.TempoRecoverySelfCheck.openSetup();
                } else if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
                    window.TempoApp.navigateTo('stress-check');
                } else {
                    window.location.hash = '#stress-check';
                }
                return;
            }

            const todayCheckin = (typeof window.TempoRecoverySelfCheck.getTodayCheckin === 'function')
                ? window.TempoRecoverySelfCheck.getTodayCheckin()
                : null;

            // Check if all active trackers have been answered today
            let allAnswered = false;
            if (todayCheckin && active.length > 0) {
                const obs = (typeof window.TempoRecoverySelfCheck.getObservationsForCheckin === 'function')
                    ? window.TempoRecoverySelfCheck.getObservationsForCheckin(todayCheckin.id)
                    : [];
                const answeredIds = new Set(obs.filter(o => o.status === 'answered' && o.value !== null && o.value !== undefined && o.value !== '').map(o => o.tracker_id));
                active.forEach(trk => {
                    if (Array.isArray(trk.alias_ids)) {
                        for (const aid of trk.alias_ids) {
                            if (answeredIds.has(aid)) {
                                answeredIds.add(trk.id);
                                break;
                            }
                        }
                    }
                });
                allAnswered = active.every(t => answeredIds.has(t.id));
            }

            if (allAnswered) {
                // If user has already completed today's check-in, open the view modal (which includes "Edit check-in")
                if (typeof window.TempoRecoverySelfCheck.openViewToday === 'function') {
                    window.TempoRecoverySelfCheck.openViewToday();
                } else if (typeof window.TempoRecoverySelfCheck.openDailyCheckin === 'function') {
                    window.TempoRecoverySelfCheck.openDailyCheckin(true);
                } else {
                    openStrack('view', { sourceContext: 'emergency' });
                }
            } else {
                // If not yet completed (or partial), open daily check-in modal directly
                if (typeof window.TempoRecoverySelfCheck.openDailyCheckin === 'function') {
                    window.TempoRecoverySelfCheck.openDailyCheckin(Boolean(todayCheckin));
                } else {
                    openStrack('checkin', { sourceContext: 'emergency' });
                }
            }
        } else {
            openStrack('checkin', { sourceContext: 'emergency' });
        }
    }

    function refreshStreakCardIfPresent() {
        const cardEl = document.querySelector('[data-tempo-ui="lower-selfcheck-streak"]');
        if (cardEl && cardEl.parentNode) {
            const temp = document.createElement('div');
            temp.innerHTML = renderLowerSelfCheckStreakCard();
            if (temp.firstElementChild) {
                cardEl.parentNode.replaceChild(temp.firstElementChild, cardEl);
            }
            if (typeof syncUmodeCreateNotesAlignment === 'function') {
                requestAnimationFrame(syncUmodeCreateNotesAlignment);
            }
        }
    }

    let isSubmittingUmodeCheckin = false;

    function getUmodeSkippedTrackers() {
        const uid = (typeof getRmodeUserId === 'function') ? getRmodeUserId() : 'local_user';
        const todayStr = (typeof getRmodeTodayDateStr === 'function') ? getRmodeTodayDateStr() : new Date().toISOString().slice(0, 10);
        const key = `tempo_umode_skipped_trackers_${uid}_${todayStr}`;
        try {
            const raw = localStorage.getItem(key);
            return raw ? JSON.parse(raw) : [];
        } catch (e) {
            return [];
        }
    }

    function addUmodeSkippedTracker(trackerId) {
        if (!trackerId) return;
        const uid = (typeof getRmodeUserId === 'function') ? getRmodeUserId() : 'local_user';
        const todayStr = (typeof getRmodeTodayDateStr === 'function') ? getRmodeTodayDateStr() : new Date().toISOString().slice(0, 10);
        const key = `tempo_umode_skipped_trackers_${uid}_${todayStr}`;
        const list = getUmodeSkippedTrackers();
        if (!list.includes(trackerId)) {
            list.push(trackerId);
            try {
                localStorage.setItem(key, JSON.stringify(list));
            } catch (e) {}
        }
    }

    function removeUmodeSkippedTracker(trackerId) {
        if (!trackerId) return;
        const uid = (typeof getRmodeUserId === 'function') ? getRmodeUserId() : 'local_user';
        const todayStr = (typeof getRmodeTodayDateStr === 'function') ? getRmodeTodayDateStr() : new Date().toISOString().slice(0, 10);
        const key = `tempo_umode_skipped_trackers_${uid}_${todayStr}`;
        let list = getUmodeSkippedTrackers();
        list = list.filter(id => id !== trackerId);
        try {
            localStorage.setItem(key, JSON.stringify(list));
        } catch (e) {}
    }

    function resetUmodeSkippedTrackers() {
        const uid = (typeof getRmodeUserId === 'function') ? getRmodeUserId() : 'local_user';
        const todayStr = (typeof getRmodeTodayDateStr === 'function') ? getRmodeTodayDateStr() : new Date().toISOString().slice(0, 10);
        const key = `tempo_umode_skipped_trackers_${uid}_${todayStr}`;
        try {
            localStorage.removeItem(key);
        } catch (e) {}
        refreshStreakCardIfPresent();
    }

    function skipUmodeCurrentSelfCheck(trackerId) {
        if (isSubmittingUmodeCheckin) return;
        if (!trackerId) return;
        isSubmittingUmodeCheckin = true;
        try {
            addUmodeSkippedTracker(trackerId);
            refreshStreakCardIfPresent();
        } catch (e) {
            console.error("Failed to skip Umode self-check tracker:", e);
        } finally {
            setTimeout(() => { isSubmittingUmodeCheckin = false; }, 200);
        }
    }

    function handleUmodeSliderInput(inputEl, trackerId) {
        if (!inputEl) return;
        const val = Math.max(0, Math.min(100, parseInt(inputEl.value, 10) || 0));
        inputEl.setAttribute('aria-valuenow', val);
        const fill = document.getElementById('umode-slider-fill');
        if (fill) fill.style.width = val + '%';
        const thumb = document.getElementById('umode-slider-thumb');
        if (thumb) thumb.style.left = val + '%';
        const badge = document.getElementById('umode-slider-badge');
        if (badge) badge.textContent = val + '%';
    }

    function handleUmodeSliderChange(inputEl, trackerId) {
        if (!inputEl) return;
        const val = Math.max(0, Math.min(100, parseInt(inputEl.value, 10) || 0));
        submitUmodeSelfCheckValue(trackerId, val, false);
    }

    function handleUmodeTrackPointer(e, trackerId) {
        const container = document.getElementById('umode-slider-track-container');
        const input = document.getElementById('umode-selfcheck-range');
        if (!container || !input) return;
        const rect = container.getBoundingClientRect();
        if (rect.width <= 0) return;
        const clientX = (e.clientX !== undefined) ? e.clientX : (e.touches && e.touches[0] ? e.touches[0].clientX : rect.left);
        const offsetX = Math.max(0, Math.min(rect.width, clientX - rect.left));
        const percent = Math.round((offsetX / rect.width) * 100);
        input.value = percent;
        handleUmodeSliderInput(input, trackerId);
        if (e.type === 'pointerup' || e.type === 'mouseup' || e.type === 'touchend') {
            handleUmodeSliderChange(input, trackerId);
        }
    }

    function confirmUmodePercentage(trackerId) {
        const input = document.getElementById('umode-selfcheck-range');
        let val = 50;
        if (input) {
            val = Math.max(0, Math.min(100, parseInt(input.value, 10) || 0));
        }
        submitUmodeSelfCheckValue(trackerId, val, true);
    }

    function confirmUmodeQuantity(trackerId) {
        const input = document.getElementById(`umode-qty-input-${trackerId}`);
        if (!input) return;
        const raw = input.value.trim();
        if (!raw || isNaN(Number(raw))) {
            input.classList.add('border-red-400', 'ring-1', 'ring-red-400');
            setTimeout(() => input.classList.remove('border-red-400', 'ring-1', 'ring-red-400'), 1500);
            return;
        }
        submitUmodeSelfCheckValue(trackerId, Number(raw), true);
    }

    function submitUmodeSelfCheckValue(trackerId, value, shouldAdvance = true) {
        if (isSubmittingUmodeCheckin) return;
        if (!trackerId || value === null || value === undefined || (typeof value === 'string' && value.trim() === '')) {
            return;
        }
        isSubmittingUmodeCheckin = true;

        try {
            if (window.TempoSelfCheckWorkspace && typeof window.TempoSelfCheckWorkspace.setTodayObservation === 'function') {
                window.TempoSelfCheckWorkspace.setTodayObservation(trackerId, value, 'answered');
            } else if (typeof saveRmodeFallbackObservation === 'function') {
                saveRmodeFallbackObservation(trackerId, value, 'answered');
            } else {
                const uid = (typeof getRmodeUserId === 'function') ? getRmodeUserId() : 'local_user';
                const todayStr = (typeof getRmodeTodayDateStr === 'function') ? getRmodeTodayDateStr() : new Date().toISOString().slice(0, 10);
                const checkinsKey = `tempo_selfcheck_checkins_${uid}`;
                const obsKey = `tempo_selfcheck_observations_${uid}`;
                let checkins = [];
                try { checkins = JSON.parse(localStorage.getItem(checkinsKey) || '[]'); } catch (e) {}
                let allObs = [];
                try { allObs = JSON.parse(localStorage.getItem(obsKey) || '[]'); } catch (e) {}
                let todayChk = checkins.find(c => c.checkin_date === todayStr);
                if (!todayChk) {
                    todayChk = {
                        id: 'chk_' + todayStr.replace(/-/g, '') + '_' + Math.random().toString(36).substr(2, 4),
                        user_id: uid,
                        checkin_date: todayStr,
                        completed_at: new Date().toISOString(),
                        created_at: new Date().toISOString(),
                        updated_at: new Date().toISOString()
                    };
                    checkins.push(todayChk);
                    localStorage.setItem(checkinsKey, JSON.stringify(checkins));
                }
                const existingIdx = allObs.findIndex(o => o.checkin_id === todayChk.id && o.tracker_id === trackerId);
                if (existingIdx !== -1) {
                    allObs[existingIdx].value = value;
                    allObs[existingIdx].status = 'answered';
                    allObs[existingIdx].updated_at = new Date().toISOString();
                } else {
                    allObs.push({
                        id: 'obs_' + Date.now() + '_' + Math.random().toString(36).substr(2, 4),
                        checkin_id: todayChk.id,
                        tracker_id: trackerId,
                        value: value,
                        status: 'answered',
                        note: '',
                        created_at: new Date().toISOString(),
                        updated_at: new Date().toISOString()
                    });
                }
                localStorage.setItem(obsKey, JSON.stringify(allObs));
            }

            // Confirm save succeeded
            let savedObs = null;
            if (typeof getRmodeTodayObservation === 'function') {
                savedObs = getRmodeTodayObservation(trackerId);
            }
            const isConfirmed = savedObs && savedObs.status === 'answered' && savedObs.value !== null && savedObs.value !== undefined;
            if (!isConfirmed) {
                console.error("Save confirmation failed for Umode check-in:", trackerId);
                if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                    window.TempoApp.showToast("Could not save check-in. Please try again.");
                }
                isSubmittingUmodeCheckin = false;
                return;
            }

            removeUmodeSkippedTracker(trackerId);
            if (typeof removeRmodeSkippedTracker === 'function') {
                removeRmodeSkippedTracker(trackerId);
            }

            if (shouldAdvance) {
                refreshStreakCardIfPresent();
            }

            try {
                window.dispatchEvent(new CustomEvent('tempo:selfcheck-updated'));
            } catch (e) {}

            if (window.TempoAlertSystem && typeof window.TempoAlertSystem.evaluateAndTriggerAlert === 'function') {
                window.TempoAlertSystem.evaluateAndTriggerAlert(trackerId);
            }
        } catch (e) {
            console.error("Failed to save Umode self-check value:", e);
            if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                window.TempoApp.showToast("Could not save check-in. Please try again.");
            }
        } finally {
            setTimeout(() => { isSubmittingUmodeCheckin = false; }, 250);
        }
    }

    function getRecentlyState() {
        if (recentlyConfigState) return recentlyConfigState;
        try {
            if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.getRecentlyState === 'function') {
                return window.TempoRecoverySelfCheck.getRecentlyState();
            }
            if (window.TempoRecoveryRecently && typeof window.TempoRecoveryRecently.getState === 'function') {
                return window.TempoRecoveryRecently.getState();
            }
            const saved = localStorage.getItem('tempo_recovery_recently_state');
            if (saved) {
                return JSON.parse(saved);
            }
        } catch (e) {}
        return { type: 'EMPTY' }; // Default honest empty for Phase 1
    }

    function setRecentlyState(state) {
        recentlyConfigState = state;
        try {
            localStorage.setItem('tempo_recovery_recently_state', JSON.stringify(state));
        } catch (e) {}
        if (activeContext === MODES.RECOVERY) renderRmodeHome();
    }

    function checkIsWeeklyReviewReady() {
        if (weeklyReviewDismissed) return false;
        if (weeklyReviewOverrideReady) return true;
        try {
            if (window.TempoWeeklyReview && typeof window.TempoWeeklyReview.isReady === 'function') {
                return window.TempoWeeklyReview.isReady();
            }
        } catch (e) {}
        return false;
    }

    function setWeeklyReviewReady(isReady) {
        weeklyReviewOverrideReady = !!isReady;
        weeklyReviewDismissed = false;
        if (activeContext === MODES.RECOVERY) renderRmodeHome();
    }

    function dismissWeeklyReviewNotice() {
        weeklyReviewDismissed = true;
        if (window.TempoWeeklyReview && typeof window.TempoWeeklyReview.getLatestEligibleWeek === 'function') {
            const wk = window.TempoWeeklyReview.getLatestEligibleWeek();
            if (wk) window.TempoWeeklyReview.snoozeOrDismissNotice(wk.start);
        }
        if (activeContext === MODES.RECOVERY) renderRmodeHome();
    }

    function dismissRecoveryIntro() {
        try {
            localStorage.setItem('tempo_recovery_intro_dismissed', 'true');
        } catch (e) {}
        const banner = document.getElementById('recovery-intro-banner');
        if (banner) {
            banner.remove();
        }
    }

    function getWorkingPlanStorageKey() {
        const uid = (window.TempoAuth && typeof window.TempoAuth.getCurrentUserId === 'function') 
            ? window.TempoAuth.getCurrentUserId() 
            : ((window.TempoPlanStore && typeof window.TempoPlanStore.getUserId === 'function') ? window.TempoPlanStore.getUserId() : 'guest');
        return (uid && uid !== 'guest') ? `tempo_working_plan_${uid}` : 'tempo_working_plan';
    }

    function getRmodeMockTasksKey() {
        const uid = (window.TempoAuth && typeof window.TempoAuth.getCurrentUserId === 'function') 
            ? window.TempoAuth.getCurrentUserId() 
            : ((window.TempoPlanStore && typeof window.TempoPlanStore.getUserId === 'function') ? window.TempoPlanStore.getUserId() : 'guest');
        return (uid && uid !== 'guest') ? `tempo_rmode_mock_tasks_${uid}` : 'tempo_rmode_mock_tasks';
    }

    function renderRmodeHome() {
        applyModeVisibility(MODES.RECOVERY);

        const rmodeBox = document.getElementById('rmode-home-content');
        if (!rmodeBox) return;

        // User-scoped active plan resolution
        const currentUserId = (window.TempoAuth && typeof window.TempoAuth.getCurrentUserId === 'function') 
            ? window.TempoAuth.getCurrentUserId() 
            : ((window.TempoPlanStore && typeof window.TempoPlanStore.getUserId === 'function') ? window.TempoPlanStore.getUserId() : 'guest');
        const isAuthenticated = !!(currentUserId && currentUserId !== 'guest');

        let confirmedPlan = null;
        if (window.TempoPlanWorkspace && typeof window.TempoPlanWorkspace.getActivePlan === 'function') {
            confirmedPlan = window.TempoPlanWorkspace.getActivePlan();
        }
        if (!confirmedPlan && window.TempoPlanStore && typeof window.TempoPlanStore.getActivePlan === 'function') {
            confirmedPlan = window.TempoPlanStore.getActivePlan('recovery') || window.TempoPlanStore.getActivePlan('emergency');
        }
        if (!confirmedPlan && window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.getConfirmedPlan === 'function') {
            confirmedPlan = window.TempoEmergencyFlow.getConfirmedPlan();
        }
        if (!confirmedPlan || (!confirmedPlan.plannedTasks && !confirmedPlan.tasks)) {
            try {
                const key = getWorkingPlanStorageKey();
                const savedPlan = localStorage.getItem(key);
                if (savedPlan) {
                    const parsed = JSON.parse(savedPlan);
                    if (parsed && ((parsed.plannedTasks && parsed.plannedTasks.length > 0) || (parsed.tasks && parsed.tasks.length > 0))) {
                        confirmedPlan = parsed;
                    }
                }
            } catch (e) {}
        }
        // Invariant: NEVER automatically insert default or sample tasks.
        // If user has not created a plan, confirmedPlan remains null.

        const todayStr = getTodayISOString();
        const profile = window.TempoAuth ? window.TempoAuth.getCurrentProfile() : null;
        const greetingInfo = getSafeGreetingInfo(profile);
        const userName = (greetingInfo && !greetingInfo.isFallback && greetingInfo.name)
            || (profile && (profile.preferredName || profile.displayName || profile.display_name || profile.full_name || profile.name))
            || 'Innie';
        const selfCheckState = getSelfCheckState();
        const recentlyState = getRecentlyState();

        rmodeBox.innerHTML = `
            <!-- ONE CONTINUOUS RECOVERY DASHBOARD -->
            <div class="space-y-10" data-tempo-ui="recovery-home-shell">
                <!-- FIRST SCREEN: Asymmetric Grid (~65% Left / ~35% Right on Desktop) -->
                <div class="recovery-home-main-grid">
                    <!-- LEFT COLUMN (~65%) -->
                    <div class="recovery-left-col space-y-4">
                        ${renderRmodeHeader(userName)}

                        ${renderSelfCheckCard(selfCheckState, greetingInfo)}
                        ${renderRecoverySupportRowHTML()}
                    </div>

                    <!-- RIGHT COLUMN (~35%) -->
                    <div class="recovery-right-col">
                        ${renderRecoveryNoteCard({ todayStr })}
                        ${renderRecentlyCard(recentlyState)}
                        
                        <!-- Prompt and mode-switch button -->
                        <div class="recovery-prompt-wrap pt-0 flex flex-col items-center text-center space-y-2.5" style="margin-top: 20px;">
                            <p class="font-bold text-base sm:text-[17px] text-[#55504A]">
                                ${window.t ? window.t('modes.recovery.transitionQuestion', {}, (isViLocale() ? 'Bạn đang cảm thấy quá tải hơn?' : 'Are things feeling more overwhelming now?')) : (isViLocale() ? 'Bạn đang cảm thấy quá tải hơn?' : 'Are things feeling more overwhelming now?')}
                            </p>
                            <button type="button" 
                                    onclick="window.TempoMode.openChangeModeModal()"
                                    class="w-full max-w-[280px] py-3 rounded-2xl font-bold text-sm sm:text-base bg-[#D79277] hover:bg-[#C68166] text-white shadow-xs border border-[#C68166]/30 transition cursor-pointer">
                                ${window.t ? window.t('modes.urgent.changeMyMode', {}, (isViLocale() ? 'Chuyển chế độ' : 'Change my mode')) : (isViLocale() ? 'Chuyển chế độ' : 'Change my mode')}
                            </button>
                        </div>
                    </div>
                </div>

                <!-- SECOND SCREEN (Continuous vertical scroll directly beneath first screen) -->
                <!-- Two-Column Section: ~65% Working Plan / ~35% Community -->
                <div class="recovery-plan-comm-grid">
                    <!-- LEFT COLUMN (~65%): Kế hoạch Làm việc của bạn -->
                    <div class="recovery-plan-col">
                        ${renderRecoveryWorkingPlanSection(confirmedPlan, todayStr)}
                    </div>

                    <!-- RIGHT COLUMN (~35%): Từ Cộng đồng Tempo -->
                    <div class="recovery-comm-col">
                        ${renderRecoveryCommunityCard()}
                    </div>
                </div>
            </div>
            <!-- RMODE TASK DETAIL MODAL ROOT -->
            <div id="rmode-task-modal-root">
                ${renderRmodeTaskDetailModalHTML()}
            </div>
        `;

        syncModeSelectorDOM(MODES.RECOVERY);

        // Also trigger community posts preview sync
        if (window.TempoCommunity && typeof window.TempoCommunity.renderRecoveryPreview === 'function') {
            window.TempoCommunity.renderRecoveryPreview();
        }

        if (typeof syncRmodeSelfCheckAlignment === 'function') {
            requestAnimationFrame(syncRmodeSelfCheckAlignment);
        }
    }

    function renderUmodeHome() {
        applyModeVisibility(MODES.UNCLEAR);

        if (window.TempoUnclearMode && typeof window.TempoUnclearMode.renderHome === 'function') {
            window.TempoUnclearMode.renderHome();
            syncModeSelectorDOM(MODES.UNCLEAR);
            return;
        }

        const umodeBox = document.getElementById('umode-home-content');
        if (!umodeBox) return;

        const todayObj = new Date();
        const formattedDate = window.TempoI18n ? window.TempoI18n.formatDate(todayObj, {
            weekday: 'short',
            month: 'short',
            day: 'numeric'
        }) : todayObj.toLocaleDateString('en-US', {
            weekday: 'short',
            month: 'short',
            day: 'numeric'
        });

        umodeBox.innerHTML = `
            <div class="relative pb-1">
                <div class="flex items-center justify-between gap-4">
                    <div id="home-mode-selector-wrapper" class="relative inline-block text-left">
                        <button id="btn-home-mode-selector" 
                                type="button" 
                                onclick="window.TempoMode.toggleModeDropdown(event)" 
                                class="px-3.5 py-1.5 rounded-full text-xs font-bold bg-[#FEF7EC] text-[#9A5B13] hover:bg-[#FDEBD0] border border-[#FDE5BE] transition flex items-center space-x-1.5 shadow-xs cursor-pointer"
                                aria-haspopup="true"
                                aria-expanded="false"
                                title="Switch Tempo Mode">
                            <span>🧭</span>
                            <span class="font-extrabold">${window.t ? window.t('modes.unclear.name', {}, 'Unclear Mode') : 'Unclear Mode'}</span>
                            <span class="text-[10px] ml-0.5 opacity-80">▾</span>
                        </button>
                        <div id="home-mode-selector-dropdown" class="hidden absolute left-0 mt-2 w-72 sm:w-80 bg-white rounded-2xl shadow-xl border border-[#EAE4DF] z-50 overflow-hidden" role="menu"></div>
                    </div>
                    <div class="text-xs font-semibold text-[#8E8A85]">
                        ${formattedDate}
                    </div>
                </div>
            </div>
        `;
        syncModeSelectorDOM(MODES.UNCLEAR);
    }

    function renderActiveModeHome() {
        renderShellIndicator();
        const curShared = getActiveSharedTool();
        if (curShared === 'ucheck' || activeSharedTool === 'ucheck' || activeContext === MODES.UNCLEAR) {
            renderUmodeHome();
            return;
        }
        switch (activeContext) {
            case MODES.EMERGENCY:
                renderEmodeHome();
                break;
            case MODES.RECOVERY:
                renderRmodeHome();
                break;
            case MODES.UNCLEAR:
                renderUmodeHome();
                break;
            default:
                restoreDefaultHome();
                break;
        }
    }

    function syncRmodeSelfCheckAlignment() {
        const selfCheck = document.querySelector('[data-tempo-ui="recovery-self-check"]');
        const recently = document.querySelector('[data-tempo-ui="recovery-recently"]');
        if (!selfCheck || !recently) return;

        if (window.innerWidth >= 1024) {
            selfCheck.style.marginTop = '';
            const scTop = selfCheck.getBoundingClientRect().top;
            const rcTop = recently.getBoundingClientRect().top;
            const diff = rcTop - scTop;
            const curMt = parseFloat(window.getComputedStyle(selfCheck).marginTop) || 0;
            selfCheck.style.marginTop = (curMt + diff) + 'px';
        } else {
            selfCheck.style.marginTop = '';
        }
    }

    function renderRmodeHeader(userName = 'Innie') {
        const isVi = isViLocale();
        const modeName = window.t ? window.t('modes.recovery.name', {}, (isVi ? 'Chế độ Hồi phục' : 'Recovery Mode')) : (isVi ? 'Chế độ Hồi phục' : 'Recovery Mode');
        const greetingText = window.t
            ? window.t('modes.recovery.greeting', { name: escapeHTML(userName) }, (isVi ? `Chào ${escapeHTML(userName)}, hôm nay bạn thế nào?` : `Hi ${escapeHTML(userName)}, how are you today?`))
            : (isVi ? `Chào ${escapeHTML(userName)}, hôm nay bạn thế nào?` : `Hi ${escapeHTML(userName)}, how are you today?`);

        return `
            <div class="relative recovery-mode-header pb-0" data-tempo-ui="recovery-header-row">
                <!-- Top Mode Selector and Greeting Stacked Group -->
                <div class="flex flex-col items-start" data-tempo-ui="recovery-header-stack" style="gap: 20px;">
                    <!-- Anchored Mode Selector Dropdown -->
                    <div id="home-mode-selector-wrapper" class="relative inline-block text-left shrink-0">
                        <button id="btn-home-mode-selector" 
                                type="button" 
                                data-tempo-ui="mode-selector-btn"
                                onclick="window.TempoMode.toggleModeDropdown(event)" 
                                class="rounded-full text-[17px] font-bold bg-[#EDF7F1] text-[#166545] hover:bg-[#DDF0E5] border border-[#CDE9DA] transition inline-flex items-center justify-center space-x-1.5 shadow-xs cursor-pointer"
                                style="height: 40px; aspect-ratio: 5.1917 / 1; padding: 0 16px;"
                                aria-haspopup="true"
                                aria-expanded="false"
                                title="${isVi ? 'Chuyển chế độ' : 'Switch Tempo Mode'}">
                            <span class="font-extrabold text-[17px]">${modeName}</span>
                            <span class="text-[10px] ml-0.5 opacity-80">▾</span>
                        </button>
                        <div id="home-mode-selector-dropdown" class="hidden absolute left-0 mt-2 w-72 sm:w-80 bg-white rounded-2xl shadow-xl border border-[#EAE4DF] z-50 overflow-hidden" role="menu"></div>
                    </div>

                    <!-- Greeting (Terracotta #D48366) directly below Mode button -->
                    <div class="recovery-greeting pb-0 pt-0" style="margin-top: 0 !important; margin-bottom: 0 !important; padding: 0 !important;">
                        <h2 class="text-[29px] sm:text-[33px] font-extrabold text-[#D48366] tracking-tight flex items-center space-x-2.5 whitespace-normal sm:whitespace-nowrap leading-none" style="line-height: 1; margin: 0 !important;">
                            <span class="text-3xl select-none leading-none">👋</span>
                            <span class="leading-none">${greetingText}</span>
                        </h2>
                    </div>
                </div>
            </div>
        `;
    }


    function renderRecoveryIntroBanner() {
        let isDismissed = false;
        try {
            isDismissed = localStorage.getItem('tempo_recovery_intro_dismissed') === 'true';
        } catch (e) {}

        if (isDismissed) return '';

        return `
            <div id="recovery-intro-banner" class="bg-[#EDF7F1] border border-[#CDE9DA] rounded-2xl p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 transition-all">
                <div class="flex items-start space-x-3.5">
                    <span class="text-xl sm:text-2xl mt-0.5 select-none">🌱</span>
                    <div class="space-y-1">
                        <h4 class="font-heading text-sm sm:text-base font-bold text-[#166545]">
                            ${window.t ? window.t('modes.recovery.name', {}, "You're in Recovery Mode") : "You're in Recovery Mode"}
                        </h4>
                        <p class="text-xs sm:text-sm text-[#2D6A4F] leading-relaxed max-w-2xl">
                            ${window.t ? window.t('modes.recovery.introBanner', {}, 'Nothing you need to complete here. Use this space to slow things down, check in when you want to, or simply take a little breathing room.') : 'Nothing you need to complete here. Use this space to slow things down, check in when you want to, or simply take a little breathing room.'}
                        </p>
                    </div>
                </div>
                <button type="button" 
                        onclick="window.TempoMode.dismissRecoveryIntro()" 
                        class="px-4 py-2 bg-white hover:bg-stone-50 text-[#166545] border border-[#CDE9DA] font-bold text-xs rounded-xl shadow-xs shrink-0 self-start sm:self-auto transition cursor-pointer">
                    ${window.t ? window.t('modes.recovery.dismissBanner', {}, 'Got it') : 'Got it'}
                </button>
            </div>
        `;
    }

    // =========================================================================
    // RMODE SEQUENTIAL DAILY SELF-CHECK & SKIP CONTROLLER
    // =========================================================================

    let isSubmittingRmodeSelfCheck = false;

    function getRmodeUserId() {
        if (window.TempoAuth && typeof window.TempoAuth.getCurrentUserId === 'function') {
            const uid = window.TempoAuth.getCurrentUserId();
            if (uid) return uid;
        }
        return 'local_user';
    }

    function getRmodeTodayDateStr() {
        return getLocalTodayISO();
    }

    function getRmodeSkippedTrackers() {
        const uid = getRmodeUserId();
        const todayStr = getRmodeTodayDateStr();
        const key = `tempo_rmode_skipped_trackers_${uid}_${todayStr}`;
        try {
            const raw = localStorage.getItem(key);
            return raw ? JSON.parse(raw) : [];
        } catch (e) {
            return [];
        }
    }

    function addRmodeSkippedTracker(trackerId) {
        if (!trackerId) return;
        const uid = getRmodeUserId();
        const todayStr = getRmodeTodayDateStr();
        const key = `tempo_rmode_skipped_trackers_${uid}_${todayStr}`;
        const list = getRmodeSkippedTrackers();
        if (!list.includes(trackerId)) {
            list.push(trackerId);
            try {
                localStorage.setItem(key, JSON.stringify(list));
            } catch (e) {}
        }
    }

    function removeRmodeSkippedTracker(trackerId) {
        if (!trackerId) return;
        const uid = getRmodeUserId();
        const todayStr = getRmodeTodayDateStr();
        const key = `tempo_rmode_skipped_trackers_${uid}_${todayStr}`;
        let list = getRmodeSkippedTrackers();
        list = list.filter(id => id !== trackerId);
        try {
            localStorage.setItem(key, JSON.stringify(list));
        } catch (e) {}
    }

    function resetRmodeSkippedTrackers() {
        const uid = getRmodeUserId();
        const todayStr = getRmodeTodayDateStr();
        const key = `tempo_rmode_skipped_trackers_${uid}_${todayStr}`;
        try {
            localStorage.removeItem(key);
        } catch (e) {}
        renderRmodeHome();
    }

    function getRmodeTodayObservation(trackerId) {
        if (window.TempoSelfCheckWorkspace && typeof window.TempoSelfCheckWorkspace.getTodayObservation === 'function') {
            const obs = window.TempoSelfCheckWorkspace.getTodayObservation(trackerId);
            if (obs) return obs;
        }
        if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.getTodayCheckin === 'function' && typeof window.TempoRecoverySelfCheck.getObservationsForCheckin === 'function') {
            const todayChk = window.TempoRecoverySelfCheck.getTodayCheckin();
            if (todayChk) {
                const obsList = window.TempoRecoverySelfCheck.getObservationsForCheckin(todayChk.id);
                const trk = (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.getTrackerById === 'function')
                    ? window.TempoRecoverySelfCheck.getTrackerById(trackerId)
                    : null;
                const aliasIds = (trk && Array.isArray(trk.alias_ids)) ? trk.alias_ids : [];
                const found = obsList.find(o => o.tracker_id === trackerId || aliasIds.includes(o.tracker_id));
                if (found) return found;
            }
        }
        const uid = getRmodeUserId();
        const todayStr = getRmodeTodayDateStr();
        const checkinsKey = `tempo_selfcheck_checkins_${uid}`;
        const obsKey = `tempo_selfcheck_observations_${uid}`;
        try {
            const rawChk = localStorage.getItem(checkinsKey) || (uid === 'local_user' ? localStorage.getItem('tempo_selfcheck_checkins') : null);
            const rawObs = localStorage.getItem(obsKey) || (uid === 'local_user' ? localStorage.getItem('tempo_selfcheck_observations') : null);
            const checkins = rawChk ? JSON.parse(rawChk) : [];
            const todayChk = checkins.find(c => c.checkin_date === todayStr);
            if (todayChk && rawObs) {
                const allObs = JSON.parse(rawObs);
                const trk = (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.getTrackerById === 'function')
                    ? window.TempoRecoverySelfCheck.getTrackerById(trackerId)
                    : null;
                const aliasIds = (trk && Array.isArray(trk.alias_ids)) ? trk.alias_ids : [];
                return allObs.find(o => o.checkin_id === todayChk.id && (o.tracker_id === trackerId || aliasIds.includes(o.tracker_id))) || null;
            }
        } catch (e) {}
        return null;
    }

    function isRmodeTrackerAnsweredToday(trackerId) {
        const obs = getRmodeTodayObservation(trackerId);
        if (!obs) return false;
        if (obs.status !== 'answered') return false;
        if (obs.value === null || obs.value === undefined || obs.value === '') return false;
        return true;
    }

    function saveRmodeFallbackObservation(trackerId, value, status = 'answered') {
        const uid = getRmodeUserId();
        const todayStr = getRmodeTodayDateStr();
        const checkinsKey = `tempo_selfcheck_checkins_${uid}`;
        const obsKey = `tempo_selfcheck_observations_${uid}`;

        let checkins = [];
        try {
            checkins = JSON.parse(localStorage.getItem(checkinsKey) || '[]');
            if (checkins.length === 0 && uid === 'local_user') {
                checkins = JSON.parse(localStorage.getItem('tempo_selfcheck_checkins') || '[]');
            }
        } catch (e) {}

        let allObs = [];
        try {
            allObs = JSON.parse(localStorage.getItem(obsKey) || '[]');
            if (allObs.length === 0 && uid === 'local_user') {
                allObs = JSON.parse(localStorage.getItem('tempo_selfcheck_observations') || '[]');
            }
        } catch (e) {}

        let todayChk = checkins.find(c => c.checkin_date === todayStr);
        if (!todayChk) {
            todayChk = {
                id: 'chk_' + todayStr.replace(/-/g, '') + '_' + Math.random().toString(36).substr(2, 4),
                user_id: uid,
                checkin_date: todayStr,
                completed_at: new Date().toISOString(),
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString()
            };
            checkins.push(todayChk);
            localStorage.setItem(checkinsKey, JSON.stringify(checkins));
            if (uid === 'local_user') localStorage.setItem('tempo_selfcheck_checkins', JSON.stringify(checkins));
        }

        const existingIdx = allObs.findIndex(o => o.checkin_id === todayChk.id && o.tracker_id === trackerId);
        if (existingIdx !== -1) {
            allObs[existingIdx].value = value;
            allObs[existingIdx].status = status;
            allObs[existingIdx].updated_at = new Date().toISOString();
        } else {
            allObs.push({
                id: 'obs_' + Date.now() + '_' + Math.random().toString(36).substr(2, 4),
                checkin_id: todayChk.id,
                tracker_id: trackerId,
                value: value,
                status: status,
                note: '',
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString()
            });
        }

        localStorage.setItem(obsKey, JSON.stringify(allObs));
        if (uid === 'local_user') localStorage.setItem('tempo_selfcheck_observations', JSON.stringify(allObs));
    }

    function submitRmodeSelfCheckValue(trackerId, value) {
        if (isSubmittingRmodeSelfCheck) return;
        isSubmittingRmodeSelfCheck = true;

        try {
            if (window.TempoSelfCheckWorkspace && typeof window.TempoSelfCheckWorkspace.setTodayObservation === 'function') {
                window.TempoSelfCheckWorkspace.setTodayObservation(trackerId, value, 'answered');
            } else {
                saveRmodeFallbackObservation(trackerId, value, 'answered');
            }

            removeRmodeSkippedTracker(trackerId);
            renderRmodeHome();
            if (typeof refreshStreakCardIfPresent === 'function') {
                refreshStreakCardIfPresent();
            }

            if (window.TempoAlertSystem && typeof window.TempoAlertSystem.evaluateAndTriggerAlert === 'function') {
                window.TempoAlertSystem.evaluateAndTriggerAlert(trackerId);
            }
        } catch (e) {
            console.error("Failed to save check-in:", e);
            if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                window.TempoApp.showToast("Could not save check-in. Please try again.");
            }
        } finally {
            setTimeout(() => { isSubmittingRmodeSelfCheck = false; }, 300);
        }
    }

    function skipRmodeCurrentSelfCheck(trackerId) {
        if (isSubmittingRmodeSelfCheck) return;
        isSubmittingRmodeSelfCheck = true;

        try {
            addRmodeSkippedTracker(trackerId);
            renderRmodeHome();
        } finally {
            setTimeout(() => { isSubmittingRmodeSelfCheck = false; }, 300);
        }
    }

    function submitRmodeQuantityValue(trackerId) {
        const input = document.getElementById(`rmode-qty-input-${trackerId}`);
        if (!input) return;
        const raw = input.value.trim();
        if (!raw) {
            input.classList.add('border-red-400', 'ring-1', 'ring-red-400');
            input.focus();
            return;
        }
        const num = parseFloat(raw);
        if (isNaN(num) || num < 0 || !isFinite(num)) {
            input.classList.add('border-red-400', 'ring-1', 'ring-red-400');
            input.focus();
            return;
        }
        input.classList.remove('border-red-400', 'ring-1', 'ring-red-400');
        submitRmodeSelfCheckValue(trackerId, num);
    }

    function renderSelfCheckCard(selfCheckState, greetingInfo) {
        const isVi = isViLocale();
        const streakCount = (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.calculateStreak === 'function')
            ? window.TempoRecoverySelfCheck.calculateStreak()
            : ((selfCheckState && typeof selfCheckState.streak === 'number') ? selfCheckState.streak : 0);

        const dailyCheckinBadgeText = window.t
            ? window.t('modes.recovery.dailyCheckinBadge', {}, (isVi ? 'CHECK-IN HẰNG NGÀY' : 'YOUR DAILY CHECK-IN'))
            : (isVi ? 'CHECK-IN HẰNG NGÀY' : 'YOUR DAILY CHECK-IN');
        const todaySelfCheckTitleText = window.t
            ? window.t('modes.recovery.todaySelfCheckTitle', {}, (isVi ? 'Self-check cho hôm nay' : 'Today’s self-check'))
            : (isVi ? 'Self-check cho hôm nay' : 'Today’s self-check');
        const streakDaysText = window.t
            ? window.t('modes.recovery.streakDays', { count: streakCount }, (isVi ? `Chuỗi ${streakCount} ngày` : `${streakCount}-day streak`))
            : (isVi ? `Chuỗi ${streakCount} ngày` : `${streakCount}-day streak`);

        let rawActiveTrackers = (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.getActiveTrackers === 'function')
            ? window.TempoRecoverySelfCheck.getActiveTrackers()
            : [];

        // Deduplicate by canonical concept
        const seenSelfCheckConcepts = new Set();
        const activeTrackers = [];
        rawActiveTrackers.forEach(trk => {
            if (!trk || !trk.name) return;
            const nameLower = trk.name.trim().toLowerCase();
            const conceptKey = nameLower.includes('tension') 
                ? 'stress_sign::tension' 
                : `${(trk.category || 'stress_sign').toLowerCase()}::${nameLower}`;
            if (!seenSelfCheckConcepts.has(conceptKey)) {
                seenSelfCheckConcepts.add(conceptKey);
                activeTrackers.push(trk);
            }
        });

        if (activeTrackers.length === 0) {
            return `
                <div class="recovery-card-selfcheck bg-[#FEFAF4] rounded-3xl p-6 sm:p-7 soft-card-shadow border border-white/60 flex flex-col justify-between lg:mt-[52px]" style="min-height: 290px; width: calc(100% - 30px); margin-inline: auto; background-color: #FEFAF4;" data-tempo-ui="recovery-self-check">
                    <div class="space-y-1">
                        <span class="text-xs sm:text-sm font-extrabold text-[#4A6B5D] uppercase tracking-wide block">${dailyCheckinBadgeText}</span>
                        <h3 class="font-heading text-2xl sm:text-3xl font-extrabold text-[#484541] tracking-tight leading-snug">${todaySelfCheckTitleText}</h3>
                        <p class="text-xs italic text-[#7B7672] font-medium">${streakDaysText}</p>
                    </div>
                    <div class="py-3 text-center space-y-1">
                        <p class="text-xs font-semibold text-[#5B5550]">${isVi ? 'Chưa có mục theo dõi nào trong hệ thống.' : 'No tracking items in your system yet.'}</p>
                        <p class="text-[11px] text-stone-400">${isVi ? 'Thêm thói quen hoặc dấu hiệu trong công cụ Tự kiểm tra để bắt đầu điểm danh tại đây.' : 'Add habits or indicators in your Self-check tool to check in here.'}</p>
                    </div>
                    <div class="pt-1 flex flex-wrap items-center gap-3" data-tempo-ui="rmode-selfcheck-empty-actions">
                        <button type="button" 
                                id="btn-rmode-add-tracking"
                                data-tempo-ui="rmode-add-tracking-btn"
                                onclick="if (window.TempoMode && typeof window.TempoMode.handleAddTrackingDirectClick === 'function') { window.TempoMode.handleAddTrackingDirectClick(); } else if (window.TempoMode && typeof window.TempoMode.openStrack === 'function') { window.TempoMode.openStrack('open', { sourceContext: 'recovery', openAdjust: true }); } else if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') { window.TempoApp.navigateTo('stress-check'); } else { window.location.hash = '#stress-check'; }"
                                class="px-5 py-2.5 rounded-xl font-bold text-xs sm:text-sm bg-white border border-[#7B9688] text-[#4A6B5D] hover:bg-[#F4F7F5] shadow-xs transition cursor-pointer">
                            ${isVi ? 'Thêm mục tracking' : 'Add Tracking'}
                        </button>
                        <button type="button" 
                                id="btn-rmode-setup-tracking"
                                data-tempo-ui="rmode-setup-tracking-btn"
                                onclick="if (window.TempoMode && typeof window.TempoMode.handleRecoveryIntroSetupClick === 'function') { window.TempoMode.handleRecoveryIntroSetupClick(); } else if (window.TempoRecoverySetup && typeof window.TempoRecoverySetup.open === 'function') { window.TempoRecoverySetup.open(1); if (typeof window.TempoRecoverySetup.goToStage === 'function') window.TempoRecoverySetup.goToStage(1); } else if (window.TempoMode && typeof window.TempoMode.openStrack === 'function') { window.TempoMode.openStrack('setup', { stage: 1 }); }"
                                class="px-5 py-2.5 rounded-xl font-bold text-xs sm:text-sm bg-[#7B9688] hover:bg-[#6D8475] text-white shadow-xs transition cursor-pointer">
                            ${isVi ? 'Thiết lập hệ thống tracking' : 'Set Up My Tracking System'}
                        </button>
                    </div>
                </div>
            `;
        }

        const answeredTrackers = activeTrackers.filter(t => isRmodeTrackerAnsweredToday(t.id));
        const answeredCount = answeredTrackers.length;
        const totalCount = activeTrackers.length;
        const progressPercent = Math.round((answeredCount / totalCount) * 100);

        const skippedIds = new Set(getRmodeSkippedTrackers());
        const skippedTrackers = activeTrackers.filter(t => !isRmodeTrackerAnsweredToday(t.id) && skippedIds.has(t.id));

        const pendingTrackers = activeTrackers.filter(t => !isRmodeTrackerAnsweredToday(t.id) && !skippedIds.has(t.id));

        // Middle Section HTML: Single current tracker OR completed state
        let middleSectionHTML = '';

        if (pendingTrackers.length > 0) {
            const currentTracker = pendingTrackers[0];
            const dotColor = currentTracker.type_color || (currentTracker.category === 'stress_sign' ? '#D48366' : (currentTracker.category === 'supportive' ? '#166545' : '#1E40AF'));
            const method = currentTracker.check_method;
            const nameLower = (currentTracker.name || '').toLowerCase();

            let controlsHTML = '';

            if (method === 'percentage' || nameLower.includes('tension')) {
                controlsHTML = `
                    <div class="space-y-1.5 pt-0.5 pb-1">
                        <div class="flex items-center justify-between text-xs">
                            <span class="text-[#7B7672] font-medium">${window.t ? window.t('modes.recovery.selectLevel', {}, (isVi ? 'Chọn mức độ:' : 'Select level:')) : (isVi ? 'Chọn mức độ:' : 'Select level:')}</span>
                            <span id="rmode-slider-val" class="font-extrabold text-[#37352F] text-sm">50%</span>
                        </div>
                        <div class="flex items-center space-x-2.5">
                            <input type="range" min="0" max="100" value="50" 
                                   id="rmode-selfcheck-range"
                                   oninput="const el = document.getElementById('rmode-slider-val'); if (el) el.textContent = this.value + '%'"
                                   class="w-full accent-[#4A6B5D] cursor-pointer">
                            <button type="button" 
                                    onclick="window.TempoMode.submitRmodeSelfCheckValue('${currentTracker.id}', parseInt(document.getElementById('rmode-selfcheck-range').value, 10))"
                                    class="px-3.5 py-1.5 rounded-xl text-xs font-bold bg-[#7B9688] hover:bg-[#6D8475] text-white transition cursor-pointer shrink-0 shadow-2xs">
                                ${window.t ? window.t('modes.recovery.save', {}, (isVi ? 'Lưu' : 'Save')) : (isVi ? 'Lưu' : 'Save')}
                            </button>
                        </div>
                    </div>
                `;
            } else if (method === 'options' || method === 'yes_no' || nameLower.includes('sleep')) {
                let opts = currentTracker.options;
                if (!opts || !Array.isArray(opts) || opts.length === 0) {
                    opts = nameLower.includes('sleep') ? ['Good', 'Not good'] : ['Yes', 'No'];
                }
                controlsHTML = `
                    <div class="pt-0.5 pb-1">
                        <div class="flex items-center flex-wrap gap-2">
                            ${opts.map(opt => `
                                <button type="button" 
                                        onclick="window.TempoMode.submitRmodeSelfCheckValue('${currentTracker.id}', '${escapeHTML(opt)}')"
                                        class="px-4 py-1.5 rounded-xl text-xs font-bold bg-white hover:bg-[#F4F7F5] border border-stone-300/80 text-[#37352F] hover:border-[#7B9688] hover:text-[#166545] transition cursor-pointer shadow-2xs">
                                    ${escapeHTML(opt)}
                                </button>
                            `).join('')}
                        </div>
                    </div>
                `;
            } else if (method === 'scale') {
                const scaleMax = currentTracker.scale_max || (currentTracker.scale_range === '1-10' ? 10 : 5);
                const scaleNums = [];
                for (let n = 1; n <= scaleMax; n++) scaleNums.push(n);
                controlsHTML = `
                    <div class="pt-0.5 pb-1">
                        <div class="flex items-center space-x-1.5 overflow-x-auto pb-0.5">
                            ${scaleNums.map(n => `
                                <button type="button" 
                                        onclick="window.TempoMode.submitRmodeSelfCheckValue('${currentTracker.id}', ${n})"
                                        class="w-8 h-8 rounded-xl text-xs font-bold bg-white hover:bg-[#F4F7F5] border border-stone-300/80 text-[#37352F] hover:border-[#7B9688] hover:text-[#166545] transition cursor-pointer flex items-center justify-center shrink-0 shadow-2xs">
                                    ${n}
                                </button>
                            `).join('')}
                        </div>
                    </div>
                `;
            } else if (method === 'quantity' || nameLower.includes('walk')) {
                const unit = currentTracker.quantity_unit || 'min';
                controlsHTML = `
                    <div class="pt-0.5 pb-1">
                        <div class="flex items-center flex-wrap gap-2">
                            <input type="number" 
                                    id="rmode-qty-input-${currentTracker.id}"
                                    placeholder="${isVi ? 'Nhập số lượng' : 'Enter quantity'}"
                                    min="0"
                                    step="any"
                                    class="w-28 sm:w-32 px-3 py-1.5 text-xs font-semibold rounded-xl border border-stone-300 focus:outline-none focus:border-[#4A6B5D] bg-white shadow-2xs">
                            <span class="text-xs font-bold text-[#5B5550]">${escapeHTML(unit)}</span>
                            <button type="button" 
                                    onclick="window.TempoMode.submitRmodeQuantityValue('${currentTracker.id}')"
                                    class="px-3.5 py-1.5 rounded-xl text-xs font-bold bg-[#7B9688] hover:bg-[#6D8475] text-white transition cursor-pointer shrink-0 shadow-2xs">
                                ${window.t ? window.t('modes.recovery.save', {}, (isVi ? 'Lưu' : 'Save')) : (isVi ? 'Lưu' : 'Save')}
                            </button>
                            <button type="button" 
                                    onclick="window.TempoMode.submitRmodeSelfCheckValue('${currentTracker.id}', 'no')"
                                    class="px-2.5 py-1.5 rounded-xl text-xs font-semibold text-stone-500 hover:text-stone-700 hover:bg-stone-100 transition cursor-pointer">
                                ${isVi ? 'Chưa làm' : "Didn't do"}
                            </button>
                        </div>
                    </div>
                `;
            } else {
                controlsHTML = `
                    <div class="pt-0.5 pb-1 flex items-center space-x-2">
                        <button type="button" 
                                onclick="window.TempoMode.submitRmodeSelfCheckValue('${currentTracker.id}', 'yes')"
                                class="px-4 py-1.5 rounded-xl text-xs font-bold bg-[#7B9688] text-white hover:bg-[#6D8475] shadow-2xs transition">
                            Check in
                        </button>
                    </div>
                `;
            }

            middleSectionHTML = `
                <div class="space-y-2 py-1">
                    <!-- Tracker Header with Color Dot & Small Secondary Skip Button -->
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-2 text-sm font-bold text-[#484541] truncate min-w-0">
                            <span class="w-2.5 h-2.5 rounded-full inline-block shrink-0" style="background-color: ${dotColor};"></span>
                            <span class="truncate">${escapeHTML(currentTracker.name)}</span>
                        </div>
                        <button type="button" 
                                onclick="window.TempoMode.skipRmodeCurrentSelfCheck('${currentTracker.id}')"
                                class="text-xs font-semibold text-[#8C8681] hover:text-[#37352F] hover:bg-stone-200/50 px-2.5 py-1 rounded-lg transition cursor-pointer shrink-0"
                                title="${isVi ? 'Bỏ qua lúc này' : 'Skip for now'}">
                            ${window.t ? window.t('modes.recovery.skip', {}, (isVi ? 'Bỏ qua' : 'Skip')) : (isVi ? 'Bỏ qua' : 'Skip')}
                        </button>
                    </div>

                    <!-- Single Interactive Control -->
                    ${controlsHTML}

                    <!-- Summary Line (without progress bar) -->
                    <div class="pt-1 flex items-center justify-between text-xs text-[#5B5550]">
                        <span>${window.t ? window.t('modes.recovery.checkinSummary', { completed: answeredCount, total: totalCount }, (isVi ? `Bạn đã check-in ${answeredCount}/${totalCount} mục hôm nay.` : `You checked on ${answeredCount}/${totalCount} things today.`)) : (isVi ? `Bạn đã check-in ${answeredCount}/${totalCount} mục hôm nay.` : `You checked on ${answeredCount}/${totalCount} things today.`)}</span>
                        ${skippedTrackers.length > 0 ? `<span class="text-[11px] text-[#8C8681]">(${skippedTrackers.length} ${isVi ? 'đã bỏ qua' : 'skipped'})</span>` : ''}
                    </div>
                </div>
            `;
        } else {
            // Completed / All Items Processed Summary State
            const allChecked = answeredCount === totalCount;
            middleSectionHTML = `
                <div class="space-y-2 py-1.5">
                    <div class="flex items-center space-x-2 text-sm font-bold ${allChecked ? 'text-[#166545]' : 'text-[#484541]'}">
                        <span class="w-2.5 h-2.5 rounded-full ${allChecked ? 'bg-[#166545]' : 'bg-[#7B9688]'} inline-block"></span>
                        <span>${allChecked ? (isVi ? 'Đã hoàn thành tất cả check-in hôm nay! 🎉' : 'All check-ins completed today! 🎉') : (isVi ? 'Đã hoàn thành check-in hôm nay' : 'Today’s check-in complete')}</span>
                    </div>

                    <!-- Summary Line (without progress bar) -->
                    <div class="pt-0.5 flex items-center justify-between text-xs text-[#5B5550]">
                        <span>${window.t ? window.t('modes.recovery.checkinSummary', { completed: answeredCount, total: totalCount }, (isVi ? `Bạn đã check-in ${answeredCount}/${totalCount} mục hôm nay.` : `You checked on ${answeredCount}/${totalCount} things today.`)) : (isVi ? `Bạn đã check-in ${answeredCount}/${totalCount} mục hôm nay.` : `You checked on ${answeredCount}/${totalCount} things today.`)}</span>
                        ${skippedTrackers.length > 0 ? `
                            <button type="button" 
                                    onclick="window.TempoMode.resetRmodeSkippedTrackers()"
                                    class="text-xs font-bold text-[#4A6B5D] hover:underline cursor-pointer">
                                ${isVi ? `Xem lại ${skippedTrackers.length} mục đã bỏ qua` : `Review ${skippedTrackers.length} skipped`}
                            </button>
                        ` : ''}
                    </div>
                </div>
            `;
        }

        return `
            <div class="recovery-card-selfcheck bg-[#FEFAF4] rounded-3xl p-6 sm:p-7 soft-card-shadow border border-white/60 flex flex-col justify-between lg:mt-[52px]" style="min-height: 290px; width: calc(100% - 30px); margin-inline: auto; background-color: #FEFAF4;" data-tempo-ui="recovery-self-check">
                <!-- Top Block: Category, Title, Streak -->
                <div class="space-y-1">
                    <span class="text-xs sm:text-sm font-extrabold text-[#4A6B5D] uppercase tracking-wide block">${dailyCheckinBadgeText}</span>
                    <h3 class="font-heading text-2xl sm:text-3xl font-extrabold text-[#484541] tracking-tight leading-snug">${todaySelfCheckTitleText}</h3>
                    <p class="text-xs italic text-[#7B7672] font-medium">${streakDaysText}</p>
                </div>

                <!-- Middle Block: Single Tracking Item OR Completed State -->
                ${middleSectionHTML}

                <!-- Bottom Block: Action Buttons -->
                <div class="pt-1 flex flex-wrap items-center gap-3">
                    <button type="button" 
                            onclick="window.TempoMode.handleSelfCheckAction('view')"
                            class="px-5 py-2.5 rounded-xl font-bold text-xs sm:text-sm bg-[#7B9688] hover:bg-[#6D8475] text-white shadow-xs transition cursor-pointer">
                        ${window.t ? window.t('modes.recovery.viewTodayCheckin', {}, (isVi ? 'Xem check-in hôm nay' : "View today's check-in")) : (isVi ? 'Xem check-in hôm nay' : "View today's check-in")}
                    </button>
                    <button type="button" 
                            onclick="if (window.TempoMode && typeof window.TempoMode.openStrack === 'function') { window.TempoMode.openStrack('open', { sourceContext: 'recovery' }); } else if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') { window.TempoApp.navigateTo('stress-check'); } else { window.location.hash = '#stress-check'; }"
                            class="px-5 py-2.5 rounded-xl font-bold text-xs sm:text-sm bg-white border border-[#7B9688] text-[#4A6B5D] hover:bg-[#F4F7F5] shadow-xs transition cursor-pointer">
                        ${window.t ? window.t('modes.recovery.editTrackingSystem', {}, (isVi ? 'Sửa tracking' : 'Edit tracking')) : (isVi ? 'Sửa tracking' : 'Edit tracking')}
                    </button>
                </div>
            </div>
        `;
    }

    // Side-by-side Quick Relief & Focus Now cards beneath Today's self-check
    function renderRecoverySupportRowHTML() {
        return `
            <div class="flex flex-col sm:flex-row items-center justify-center gap-4 sm:gap-5 w-full recovery-support-row" data-tempo-ui="recovery-support" style="margin-left: auto; margin-right: auto;">
                <!-- Tool 1: Quick Relief -->
                ${renderQuickReliefCardHTML()}

                <!-- Tool 2: Focus Now -->
                ${renderFocusNowCardHTML()}
            </div>
        `;
    }

    function getAuthoritativeTrackerObservations(trackerOrId) {
        const uid = (window.TempoAuth && typeof window.TempoAuth.getCurrentUserId === 'function')
            ? (window.TempoAuth.getCurrentUserId() || 'local_user')
            : 'local_user';
        const checkinsKey = `tempo_selfcheck_checkins_${uid}`;
        const obsKey = `tempo_selfcheck_observations_${uid}`;

        let checkins = [];
        let allObs = [];
        try {
            checkins = JSON.parse(localStorage.getItem(checkinsKey) || (uid === 'local_user' ? (localStorage.getItem('tempo_selfcheck_checkins') || '[]') : '[]'));
            allObs = JSON.parse(localStorage.getItem(obsKey) || (uid === 'local_user' ? (localStorage.getItem('tempo_selfcheck_observations') || '[]') : '[]'));
        } catch (e) {}

        const dateMap = {};
        if (Array.isArray(checkins)) {
            checkins.forEach(c => {
                if (c && c.id && c.checkin_date) {
                    dateMap[c.id] = c.checkin_date;
                }
            });
        }

        const todayStr = (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.getTodayDateStr === 'function')
            ? window.TempoRecoverySelfCheck.getTodayDateStr()
            : getLocalTodayISO();

        if (!Array.isArray(allObs)) return [];

        const trackerId = (trackerOrId && typeof trackerOrId === 'object') ? trackerOrId.id : trackerOrId;
        const trackerObj = (trackerOrId && typeof trackerOrId === 'object')
            ? trackerOrId
            : (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.getTrackerById === 'function' ? window.TempoRecoverySelfCheck.getTrackerById(trackerId) : null);

        const aliasIds = new Set();
        if (trackerId) aliasIds.add(trackerId);
        if (trackerObj && Array.isArray(trackerObj.alias_ids)) {
            trackerObj.alias_ids.forEach(aid => {
                if (aid) aliasIds.add(aid);
            });
        }

        const matchedObs = allObs
            .filter(o => o && aliasIds.has(o.tracker_id) && o.status === 'answered' && o.value !== null && o.value !== undefined && o.value !== '')
            .map(o => ({
                ...o,
                date: o.date || (o.checkin_id && dateMap[o.checkin_id]) || todayStr
            }))
            .filter(o => o.date <= todayStr);

        // Deduplicate observations by date (keep the most recently updated observation per calendar date)
        const obsByDate = new Map();
        matchedObs.forEach(o => {
            const dateKey = o.date;
            const existing = obsByDate.get(dateKey);
            if (!existing) {
                obsByDate.set(dateKey, o);
            } else {
                const existingTime = existing.updated_at || existing.created_at || '';
                const newTime = o.updated_at || o.created_at || '';
                if (newTime >= existingTime) {
                    obsByDate.set(dateKey, o);
                }
            }
        });

        return Array.from(obsByDate.values())
            .sort((a, b) => (a.date || '').localeCompare(b.date || ''));
    }

    function getWeeklyReportCountdownText() {
        const isVi = isViLocale();
        const now = new Date();
        const day = now.getDay(); // 0 is Sunday, 1 is Monday, ..., 6 is Saturday
        // Weekly review cycle in Tempo runs Monday to Sunday.
        // The weekly report is available at the end of the weekly cycle (Sunday).
        const days = (7 - day) % 7;
        if (days === 0) {
            return window.t
                ? window.t('modes.recovery.weeklyReportReadyToday', {}, (isVi ? 'Báo cáo tuần của bạn đã sẵn sàng hôm nay.' : 'Your weekly report is ready today.'))
                : (isVi ? 'Báo cáo tuần của bạn đã sẵn sàng hôm nay.' : 'Your weekly report is ready today.');
        }
        return window.t
            ? window.t('modes.recovery.weeklyReportCountdown', { days, s: days === 1 ? '' : 's' }, (isVi ? `Báo cáo tuần sẽ sẵn sàng trong ${days} ngày nữa.` : `${days} day${days === 1 ? '' : 's'} until your weekly report.`))
            : (isVi ? `Báo cáo tuần sẽ sẵn sàng trong ${days} ngày nữa.` : `${days} day${days === 1 ? '' : 's'} until your weekly report.`);
    }

    function calculateTrackingSummaryFallback(tracker, observations, isVi) {
        let method = 'percentage';
        if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.resolveTrackerMethod === 'function') {
            method = window.TempoRecoverySelfCheck.resolveTrackerMethod(tracker);
        } else if (tracker) {
            const rawMethod = tracker.check_method || tracker.checkMethod || tracker.method || tracker.tracking_method;
            if (rawMethod) {
                const norm = String(rawMethod).trim().toLowerCase().replace(/[-\s]/g, '_');
                if (norm === 'percentage' || norm === 'percent') method = 'percentage';
                else if (norm === 'scale') method = 'scale';
                else if (norm === 'quantity') method = 'quantity';
                else if (norm === 'options') method = 'options';
                else if (norm === 'yes_no' || norm === 'yesno' || norm === 'boolean') method = 'yes_no';
                else method = norm;
            } else {
                const nameLower = (tracker.name || '').trim().toLowerCase();
                if (nameLower.includes('tension')) {
                    method = 'percentage';
                } else if (tracker.scale_max !== undefined || tracker.scale_min !== undefined || tracker.scale_range) {
                    method = 'scale';
                } else if (tracker.quantity_unit !== undefined && tracker.quantity_unit !== null && tracker.quantity_unit !== '') {
                    method = 'quantity';
                } else if (Array.isArray(tracker.options) && tracker.options.length > 0) {
                    method = 'options';
                } else {
                    method = 'percentage';
                }
            }
        }

        let metricLabel = isVi ? 'Tỷ lệ phản hồi' : 'Response distribution';
        if (method === 'percentage') metricLabel = isVi ? 'Mức trung bình' : 'Average level';
        else if (method === 'scale') metricLabel = isVi ? 'Điểm trung bình' : 'Average score';
        else if (method === 'quantity') metricLabel = isVi ? 'Tổng lượng ghi nhận' : 'Total recorded';
        else if (method === 'options') metricLabel = isVi ? 'Tỷ lệ lựa chọn' : 'Option distribution';

        const validObs = (observations || []).filter(o => 
            o && o.status === 'answered' && o.value !== null && o.value !== undefined && o.value !== ''
        );

        if (validObs.length === 0) {
            return { method, metricLabel, metricValue: '—', hasData: false, count: 0 };
        }

        if (method === 'percentage') {
            const nums = [];
            validObs.forEach(o => {
                const n = parseFloat(String(o.value).replace('%', '').trim());
                if (!isNaN(n)) nums.push(n);
            });
            if (nums.length === 0) return { method, metricLabel, metricValue: '—', hasData: false, count: 0 };
            const avg = Math.round(nums.reduce((a, b) => a + b, 0) / nums.length);
            return { method, metricLabel, metricValue: `${avg}%`, hasData: true, count: nums.length };
        }

        if (method === 'scale') {
            const nums = [];
            validObs.forEach(o => {
                const n = parseFloat(o.value);
                if (!isNaN(n)) nums.push(n);
            });
            if (nums.length === 0) return { method, metricLabel, metricValue: '—', hasData: false, count: 0 };
            const max = (tracker && tracker.scale_max !== undefined) ? tracker.scale_max : 5;
            const avg = nums.reduce((a, b) => a + b, 0) / nums.length;
            const avgStr = Number.isInteger(avg) ? `${avg}` : avg.toFixed(1);
            return { method, metricLabel, metricValue: `${avgStr}/${max}`, hasData: true, count: nums.length };
        }

        if (method === 'quantity') {
            const nums = [];
            let foundUnit = (tracker && tracker.quantity_unit) ? tracker.quantity_unit : null;
            validObs.forEach(o => {
                if (o.value === 'no' || o.value === false) return;
                const n = parseFloat(o.value);
                if (!isNaN(n)) {
                    nums.push(n);
                    if (!foundUnit && o.quantity_unit) foundUnit = o.quantity_unit;
                }
            });
            if (nums.length === 0) return { method, metricLabel, metricValue: '—', hasData: false, count: 0 };
            const tot = nums.reduce((a, b) => a + b, 0);
            const displayTot = Number.isInteger(tot) ? tot : Number(tot.toFixed(2));
            const unit = foundUnit ? ` ${foundUnit}` : '';
            return { method, metricLabel, metricValue: `${displayTot}${unit}`, hasData: true, count: nums.length };
        }

        // Canonical key normalizer: trims, lowercases, replaces underscores & hyphens with single spaces
        function canonicalizeOptionKey(str) {
            if (str === null || str === undefined) return '';
            return String(str)
                .trim()
                .toLowerCase()
                .replace(/[-_]+/g, ' ')
                .replace(/\s+/g, ' ');
        }

        // Match observation value to an option in optList (resolving not_good <-> Not good, yes/no <-> Good/Not good)
        function matchOptionToPredefined(val, options) {
            if (val === null || val === undefined || !Array.isArray(options) || options.length === 0) return null;
            const valStr = String(val).trim();
            const canonVal = canonicalizeOptionKey(valStr);
            if (!canonVal) return null;

            // 1. Direct case-insensitive match
            const direct = options.find(opt => String(opt).trim().toLowerCase() === valStr.toLowerCase());
            if (direct) return direct;

            // 2. Canonical key match (handles not_good <-> Not good, not-good <-> not good)
            const canonMatch = options.find(opt => canonicalizeOptionKey(opt) === canonVal);
            if (canonMatch) return canonMatch;

            // 3. Predefined alias mappings (e.g. good <-> yes, not_good <-> no)
            for (const opt of options) {
                const canonOpt = canonicalizeOptionKey(opt);
                if (canonOpt === 'good' || canonOpt === 'tốt') {
                    if (['good', 'tốt', 'tot', 'yes', 'có', 'co', 'true'].includes(canonVal)) return opt;
                } else if (canonOpt === 'not good' || canonOpt === 'chưa tốt' || canonOpt === 'chua tot') {
                    if (['not good', 'not_good', 'not-good', 'chưa tốt', 'chua tot', 'chua_tot', 'no', 'không', 'khong', 'false'].includes(canonVal)) return opt;
                } else if (canonOpt === 'yes' || canonOpt === 'có') {
                    if (['yes', 'có', 'co', 'good', 'tốt', 'tot', 'true'].includes(canonVal)) return opt;
                } else if (canonOpt === 'no' || canonOpt === 'không') {
                    if (['no', 'không', 'khong', 'not good', 'not_good', 'not-good', 'chưa tốt', 'chua tot', 'false'].includes(canonVal)) return opt;
                }
            }

            return null;
        }

        if (method === 'options') {
            const total = validObs.length;
            let optList = (tracker && Array.isArray(tracker.options) && tracker.options.length > 0) ? [...tracker.options] : [];
            if (optList.length === 0) {
                const nameLower = (tracker && tracker.name || '').toLowerCase();
                if (nameLower.includes('sleep') || nameLower.includes('giấc ngủ')) {
                    optList = ['Good', 'Not good'];
                }
            }

            // Deduplicate configured optList itself in case of duplicate entries
            const deduplicatedOpts = [];
            optList.forEach(opt => {
                const canon = canonicalizeOptionKey(opt);
                if (!deduplicatedOpts.some(existing => canonicalizeOptionKey(existing) === canon)) {
                    deduplicatedOpts.push(opt);
                }
            });
            optList = deduplicatedOpts;

            // Discover any genuinely new distinct custom options in observations
            validObs.forEach(o => {
                const s = String(o.value).trim();
                if (!s) return;
                const matched = matchOptionToPredefined(s, optList);
                if (!matched) {
                    const canon = canonicalizeOptionKey(s);
                    const alreadyPresent = optList.some(existing => canonicalizeOptionKey(existing) === canon);
                    if (!alreadyPresent) {
                        let pretty = s;
                        if (pretty.includes('_') || pretty.includes('-')) {
                            pretty = pretty.replace(/[-_]+/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
                        }
                        optList.push(pretty);
                    }
                }
            });

            // If still empty, fallback
            if (optList.length === 0) {
                optList = ['Good', 'Not good'];
            }

            // Aggregate counts: map each observation to its normalized option
            const counts = {};
            optList.forEach(opt => counts[opt] = 0);
            validObs.forEach(o => {
                const valStr = String(o.value).trim();
                const matched = matchOptionToPredefined(valStr, optList);
                if (matched && counts[matched] !== undefined) {
                    counts[matched]++;
                } else {
                    const canon = canonicalizeOptionKey(valStr);
                    const matchedCanon = optList.find(opt => canonicalizeOptionKey(opt) === canon);
                    if (matchedCanon && counts[matchedCanon] !== undefined) {
                        counts[matchedCanon]++;
                    } else if (counts[valStr] !== undefined) {
                        counts[valStr]++;
                    } else {
                        counts[valStr] = 1;
                    }
                }
            });

            // Display format: display only option names and percentages separated by ' · '
            // Example: Good (50%) · Not good (50%)
            const parts = optList.map(opt => {
                const c = counts[opt] || 0;
                const pct = total > 0 ? Math.round((c / total) * 100) : 0;
                return `${opt} (${pct}%)`;
            });
            return { method, metricLabel, metricValue: parts.join(' · '), hasData: true, count: total, counts, options: optList };
        }

        // yes_no
        const total = validObs.length;
        let yesCount = 0;
        let noCount = 0;
        validObs.forEach(o => {
            const v = typeof o.value === 'boolean' ? o.value : String(o.value).trim().toLowerCase();
            if (v === true || v === 'yes' || v === 'true' || v === 'có' || v === 'good' || v === 'tốt') yesCount++;
            else if (v === false || v === 'no' || v === 'false' || v === 'không' || v === 'not good' || v === 'not_good' || v === 'not-good' || v === 'chưa tốt' || v === 'chua tot' || v === 'chua_tot') noCount++;
            else if (v) yesCount++; else noCount++;
        });
        const totalYesNo = yesCount + noCount;
        if (totalYesNo === 0) return { method: 'yes_no', metricLabel, metricValue: '—', hasData: false, count: 0 };
        const yesPct = (yesCount / totalYesNo) * 100;
        const noPct = (noCount / totalYesNo) * 100;
        const yesPctStr = Number.isInteger(yesPct) ? `${yesPct}%` : `${yesPct.toFixed(1)}%`;
        const noPctStr = Number.isInteger(noPct) ? `${noPct}%` : `${noPct.toFixed(1)}%`;
        const yesLabel = isVi ? 'Có' : 'Yes';
        const noLabel = isVi ? 'Không' : 'No';
        return {
            method: 'yes_no',
            metricLabel,
            metricValue: `${yesLabel} – ${yesPctStr} (${yesCount}/${totalYesNo}), ${noLabel} – ${noPctStr} (${noCount}/${totalYesNo})`,
            hasData: true,
            count: totalYesNo
        };
    }

    function renderRecentlyCard(recentlyState) {
        const isVi = isViLocale();
        let activeTrackers = [];
        if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.getActiveTrackers === 'function') {
            activeTrackers = window.TempoRecoverySelfCheck.getActiveTrackers();
        } else {
            try {
                const uid = (window.TempoAuth && typeof window.TempoAuth.getCurrentUserId === 'function')
                    ? (window.TempoAuth.getCurrentUserId() || 'local_user')
                    : 'local_user';
                const raw = localStorage.getItem(`tempo_selfcheck_trackers_${uid}`) || localStorage.getItem('tempo_selfcheck_trackers');
                if (raw) {
                    const parsed = JSON.parse(raw);
                    activeTrackers = Array.isArray(parsed) ? parsed.filter(t => !t.archived && !t.is_archived) : [];
                }
            } catch (e) {}
        }

        // Defensive deduplication by canonical tracker concept
        const seenConcepts = new Set();
        const uniqueActiveTrackers = [];
        activeTrackers.forEach(trk => {
            if (!trk || !trk.name) return;
            const nameLower = trk.name.trim().toLowerCase();
            const conceptKey = nameLower.includes('tension') 
                ? 'stress_sign::tension' 
                : `${(trk.category || 'stress_sign').toLowerCase()}::${nameLower}`;
            if (!seenConcepts.has(conceptKey)) {
                seenConcepts.add(conceptKey);
                uniqueActiveTrackers.push(trk);
            }
        });
        activeTrackers = uniqueActiveTrackers;

        const countdownText = getWeeklyReportCountdownText();

        let itemsHTML = '';
        if (activeTrackers.length === 0) {
            itemsHTML = `
                <div class="py-3 text-center">
                    <p class="text-xs text-[#7B7672]">${isVi ? 'Không có mục tracking nào đang hoạt động.' : 'No active tracking items.'}</p>
                </div>
            `;
        } else {
            itemsHTML = activeTrackers.map(tracker => {
                const nameLower = (tracker.name || '').toLowerCase();
                const dotColor = tracker.type_color || (
                    tracker.category === 'stress_sign' ? '#D48366' :
                    (nameLower.includes('sleep') ? '#5A9E75' :
                    (tracker.category === 'supportive' ? '#5A9E75' : '#7B9688'))
                );

                const observations = getAuthoritativeTrackerObservations(tracker);
                const summary = (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.calculateTrackingSummary === 'function')
                    ? window.TempoRecoverySelfCheck.calculateTrackingSummary(tracker, observations, { isVi })
                    : calculateTrackingSummaryFallback(tracker, observations, isVi);

                const description = summary.metricLabel;
                const formattedValue = summary.hasData
                    ? escapeHTML(summary.metricValue)
                    : '<span class="text-[#8E8A85] text-sm font-normal">—</span>';

                return `
                    <div class="flex items-start justify-between gap-2">
                        <div class="space-y-0.5 min-w-0">
                            <div class="flex items-center space-x-2 text-sm font-bold text-[#484541]">
                                <span class="w-2.5 h-2.5 rounded-full inline-block shrink-0" style="background-color: ${dotColor};"></span>
                                <span class="truncate">${escapeHTML(tracker.name)}</span>
                            </div>
                            <p class="text-xs text-[#7B7672] pl-4.5">${description}</p>
                        </div>
                        <div class="text-xs sm:text-sm font-extrabold text-[#4A6B5D] text-right shrink-0 max-w-[65%] leading-tight pt-0.5">
                            ${formattedValue}
                        </div>
                    </div>
                `;
            }).join('');
        }

        return `
            <div class="recovery-card-recently bg-[#FEFAF4] rounded-3xl p-6 shadow-xs border border-white/60 flex flex-col mt-2.5" style="margin-top: 10px; background-color: #FEFAF4; height: 329px; min-height: 329px; max-height: 329px; box-sizing: border-box;" data-tempo-ui="recovery-recently">
                <!-- Fixed Header -->
                <div class="shrink-0 space-y-3">
                    <div class="flex items-center justify-between pb-1">
                        <h4 class="font-heading text-xl font-extrabold text-[#484541]">
                            ${window.t ? window.t('modes.recovery.recentlyTitle', {}, (isVi ? 'Gần đây' : 'Recently')) : (isVi ? 'Gần đây' : 'Recently')}
                        </h4>
                        <button type="button" 
                                onclick="if (window.TempoMode && typeof window.TempoMode.openStrack === 'function') { window.TempoMode.openStrack('open', { sourceContext: 'recovery' }); } else if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') { window.TempoApp.navigateTo('stress-check'); } else { window.location.hash = '#stress-check'; }"
                                class="px-3 py-1 rounded-full text-xs font-bold bg-[#7D9485] hover:bg-[#6D8475] text-white shadow-2xs transition cursor-pointer">
                            ${window.t ? window.t('modes.recovery.adjustTracking', {}, (isVi ? 'Chỉnh sửa tracking' : 'Adjust Tracking')) : (isVi ? 'Chỉnh sửa tracking' : 'Adjust Tracking')}
                        </button>
                    </div>

                    <!-- Divider line -->
                    <div class="border-b border-[#F0EBE6]"></div>
                </div>

                <!-- Scrollable Metrics Content -->
                <div class="flex-1 min-h-0 overflow-y-auto overflow-x-hidden pt-3 pb-1 space-y-3 pr-1" data-tempo-ui="recently-metrics-scroll" style="scrollbar-width: thin;">
                    ${itemsHTML}
                </div>

                <!-- Fixed Footer -->
                <div class="pt-3 text-center text-xs font-bold text-[#55504A] shrink-0" data-tempo-ui="recently-countdown-footer">
                    ${countdownText}
                </div>
            </div>
        `;
    }

    function renderRecoveryNoteCard(ctx) {
        return renderEmodeCreateNotesCard(ctx);
    }

    // Canonical task completion status evaluator: strictly source of truth
    function isTaskExplicitlyCompleted(taskItem) {
        if (!taskItem) return false;
        const task = (taskItem && taskItem.task) ? taskItem.task : taskItem;

        // 1. Direct boolean property
        if (task.completed === true || taskItem.completed === true) return true;
        if (task.completed === false || taskItem.completed === false) return false;

        // 2. String representation ("true" / "false")
        if (task.completed === 'true' || taskItem.completed === 'true') return true;
        if (task.completed === 'false' || taskItem.completed === 'false') return false;

        // 3. Execution / progress status
        const status = String(task.executionStatus || task.execution_status || task.status || taskItem.executionStatus || taskItem.status || '').toLowerCase();
        if (status === 'completed' || status === 'done') return true;
        if (status === 'pending' || status === 'in_progress' || status === 'active' || status === 'not_started') return false;

        // 4. Default: strictly NOT completed (never infer completion from missing value, position, or mock state)
        return false;
    }

    function formatPlanDateHeader(dateStr, fallbackLabel) {
        if (!dateStr || typeof dateStr !== 'string') return fallbackLabel || (isViLocale() ? 'Đã lên lịch' : 'Scheduled');
        const clean = dateStr.split(/[T ]/)[0];
        if (window.TempoI18n && typeof window.TempoI18n.formatCalendarDate === 'function') {
            return window.TempoI18n.formatCalendarDate(clean, isViLocale() ? 'vi' : 'en');
        }
        return fallbackLabel || dateStr;
    }

    function renderRecoveryWorkingPlanSection(confirmedPlan, todayStr) {
        if (!todayStr) todayStr = getTodayISOString();

        // Shared plan resolution
        function hasValidTasks(p) {
            return Boolean(p && (
                (Array.isArray(p.plannedTasks) && p.plannedTasks.length > 0) ||
                (Array.isArray(p.tasks) && p.tasks.length > 0) ||
                (Array.isArray(p.unarrangedTasks) && p.unarrangedTasks.length > 0)
            ));
        }

        let plan = hasValidTasks(confirmedPlan) ? confirmedPlan : null;
        if (!plan && window.TempoPlanWorkspace && typeof window.TempoPlanWorkspace.getActivePlan === 'function') {
            const p = window.TempoPlanWorkspace.getActivePlan();
            if (hasValidTasks(p)) plan = p;
        }
        if (!plan && window.TempoPlanStore && typeof window.TempoPlanStore.getActivePlan === 'function') {
            const p = window.TempoPlanStore.getActivePlan('recovery') || window.TempoPlanStore.getActivePlan('emergency');
            if (hasValidTasks(p)) plan = p;
        }
        if (!plan && window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.getConfirmedPlan === 'function') {
            const p = window.TempoEmergencyFlow.getConfirmedPlan();
            if (hasValidTasks(p)) plan = p;
        }
        if (!plan) {
            try {
                const key = getWorkingPlanStorageKey();
                const savedPlan = localStorage.getItem(key);
                if (savedPlan) {
                    const parsed = JSON.parse(savedPlan);
                    if (hasValidTasks(parsed)) plan = parsed;
                }
            } catch (e) {}
        }

        let plannedList = [];
        if (plan && Array.isArray(plan.plannedTasks) && plan.plannedTasks.length > 0) {
            plannedList = plan.plannedTasks;
        } else if (plan && Array.isArray(plan.tasks) && plan.tasks.length > 0) {
            plannedList = plan.tasks.map((t, idx) => ({
                dayDate: t.scheduledDate || t.deadlineDate || (idx < 2 ? todayStr : null),
                task: t
            }));
        }

        const unarrangedList = (plan && Array.isArray(plan.unarrangedTasks)) ? plan.unarrangedTasks : [];
        const completedList = (plan && (Array.isArray(plan.completedTasks) ? plan.completedTasks : (Array.isArray(plan.doneTasks) ? plan.doneTasks : []))) || [];

        let allItems = [];
        const seenTaskIds = new Set();

        if (plannedList.length > 0) {
            plannedList.forEach((pt, index) => {
                const t = (pt && pt.task) ? pt.task : (pt || {});
                const taskId = t.id || pt.id || `task-${index}`;
                seenTaskIds.add(String(taskId));
                const isToday = (pt.dayDate === todayStr);
                const isCompleted = isTaskExplicitlyCompleted(pt);
                const subCount = (Array.isArray(t.subtasks) && t.subtasks.length > 0) ? t.subtasks.length : 0;
                const subDone = (Array.isArray(t.subtasks) && t.subtasks.length > 0) ? t.subtasks.filter(s => isTaskExplicitlyCompleted(s)).length : 0;
                const targetDayDate = pt.dayDate || t.scheduledDate || (isToday ? todayStr : null);
                const schedDateLabel = targetDayDate ? formatScheduledDateLabel(targetDayDate, isViLocale()) : '';
                const headerDateLabel = schedDateLabel || (targetDayDate ? formatPlanDateHeader(targetDayDate, targetDayDate) : (isViLocale() ? 'Lịch linh hoạt' : 'Flexible schedule'));

                let timeHeader = pt.timeBlock;
                if (!timeHeader) {
                    if (pt.startTime && pt.endTime) {
                        timeHeader = `${headerDateLabel}, ${formatTime12H(pt.startTime)} to ${formatTime12H(pt.endTime)}`;
                    } else if (pt.startTime) {
                        timeHeader = `${headerDateLabel}, ${formatTime12H(pt.startTime)}`;
                    } else if (pt.dayDate) {
                        timeHeader = `${headerDateLabel}, ${isViLocale() ? 'Đã lên lịch' : 'Scheduled'}`;
                    } else {
                        timeHeader = isViLocale() ? 'Lịch linh hoạt' : 'Flexible schedule';
                    }
                }

                let tag = 'Later';
                let tagClass = 'bg-[#E2EDF2] text-[#4F7A8A]';
                if (t.userLabel === 'Now' || pt.executionBadge === 'Now' || t.priorityCategory === 'DO_FIRST' || (isToday && index === 0)) {
                    tag = 'Now';
                    tagClass = 'bg-[#D79277] text-white';
                } else if (t.userLabel === 'Then' || (isToday && index === 1)) {
                    tag = 'Then';
                    tagClass = 'bg-[#F7E7D4] text-[#A6753A]';
                }

                let dueDateStr = isViLocale() ? 'Deadline: Sắp tới' : 'Deadline: Upcoming';
                if (t.dueDate) {
                    dueDateStr = `Deadline: ${t.dueDate}`;
                } else if (t.deadlineDate) {
                    const formattedDDate = formatPlanDateHeader(t.deadlineDate, t.deadlineDate);
                    const timePart = t.deadlineTime ? ` - ${formatTime12H(t.deadlineTime)}` : '';
                    dueDateStr = `Deadline: ${formattedDDate}${timePart}`;
                } else if (t.deadline) {
                    dueDateStr = `Deadline: ${t.deadline}`;
                }

                const taskIsOverdue = isTaskOverdue(t, plan);
                const taskIsMissed = !taskIsOverdue && isTaskMissedSchedule(pt, plan);

                allItems.push({
                    id: taskId,
                    task: t,
                    name: t.name || t.title || 'Untitled Task',
                    date: targetDayDate,
                    dayLabel: pt.dayLabel || headerDateLabel,
                    headerDateLabel: headerDateLabel,
                    timeHeader: timeHeader,
                    tag: tag,
                    tagClass: tagClass,
                    dueDate: dueDateStr,
                    isOverdue: taskIsOverdue,
                    isMissedSchedule: taskIsMissed,
                    subtasksText: `${subDone}/${subCount} ${isViLocale() ? 'bước nhỏ' : 'subtasks'}`,
                    completed: isCompleted
                });
            });
        }

        // Include any explicitly completed unarranged tasks in allItems so they show up in Done column
        unarrangedList.forEach((u, uIdx) => {
            const t = (u && u.task) ? u.task : u;
            const taskId = t.id || u.id || `unarranged-${uIdx}`;
            if (seenTaskIds.has(String(taskId))) return;
            const isCompleted = isTaskExplicitlyCompleted(u);
            if (isCompleted) {
                seenTaskIds.add(String(taskId));
                const subCount = (Array.isArray(t.subtasks) && t.subtasks.length > 0) ? t.subtasks.length : 0;
                const subDone = (Array.isArray(t.subtasks) && t.subtasks.length > 0) ? t.subtasks.filter(s => isTaskExplicitlyCompleted(s)).length : 0;
                allItems.push({
                    id: taskId,
                    task: t,
                    name: t.name || t.title || 'Untitled Task',
                    date: t.deadlineDate || todayStr,
                    dayLabel: 'Flexible',
                    headerDateLabel: 'Completed',
                    timeHeader: 'Flexible Schedule',
                    tag: 'Done',
                    tagClass: 'bg-[#E8EFE8] text-[#556B54]',
                    dueDate: t.deadlineDate ? `Deadline: ${formatPlanDateHeader(t.deadlineDate, t.deadlineDate)}` : (isViLocale() ? 'Chưa có deadline' : 'Flexible schedule'),
                    subtasksText: `${subDone}/${subCount} subtasks`,
                    completed: true
                });
            }
        });

        // Also include any tasks from plan.completedTasks or plan.doneTasks if not already present
        completedList.forEach((c, cIdx) => {
            const t = (c && c.task) ? c.task : c;
            const taskId = t.id || c.id || `completed-${cIdx}`;
            if (seenTaskIds.has(String(taskId))) return;
            seenTaskIds.add(String(taskId));
            const subCount = (Array.isArray(t.subtasks) && t.subtasks.length > 0) ? t.subtasks.length : 0;
            const subDone = (Array.isArray(t.subtasks) && t.subtasks.length > 0) ? t.subtasks.filter(s => isTaskExplicitlyCompleted(s)).length : 0;
            allItems.push({
                id: taskId,
                task: t,
                name: t.name || t.title || 'Untitled Task',
                date: c.dayDate || t.deadlineDate || todayStr,
                dayLabel: c.dayLabel || 'Completed',
                headerDateLabel: 'Completed',
                timeHeader: 'Completed Task',
                tag: 'Done',
                tagClass: 'bg-[#E8EFE8] text-[#556B54]',
                dueDate: t.deadlineDate ? `Deadline: ${formatPlanDateHeader(t.deadlineDate, t.deadlineDate)}` : (isViLocale() ? 'Hoàn thành' : 'Completed'),
                subtasksText: `${subDone}/${subCount} subtasks`,
                completed: true
            });
        });

        // Case 1: User has never created a Working Plan or has no tasks
        if (allItems.length === 0) {
            renderedRmodeTasksMap.clear();
            return `
                <div class="recovery-working-plan-card bg-[#FEFAF4] rounded-3xl p-6 sm:p-7 shadow-xs border border-white/60 space-y-4 max-w-full min-w-0" data-tempo-ui="recovery-working-plan" id="recovery-working-plan">
                    <!-- Header -->
                    <div class="flex items-center justify-between pb-1 shrink-0">
                        <h3 class="font-heading text-2xl font-extrabold text-[#484541] tracking-tight">
                            <span class="sr-only">${isViLocale() ? 'Kế hoạch làm việc của bạn - ' : 'Your plan for today - '}</span>${isViLocale() ? (window.t ? window.t('modes.urgent.workingPlanTitle', {}, 'Working Plan') : 'Working Plan') : 'Working Plan'}
                        </h3>
                        <button type="button"
                                onclick="if (window.TempoRecoverySetup && typeof window.TempoRecoverySetup.promptCreatePlan === 'function') { window.TempoRecoverySetup.promptCreatePlan(); } else if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') { window.TempoApp.navigateTo('plan-workspace'); } else { window.location.hash = '#plan-workspace'; }"
                                class="px-4 py-1.5 rounded-full text-xs font-bold bg-[#D79277] hover:bg-[#C68166] text-white shadow-2xs transition cursor-pointer">
                            <span class="sr-only">${isViLocale() ? 'Tạo kế hoạch - ' : 'Create Plan - '}</span><span>+ ${isViLocale() ? 'Tạo plan' : 'Create Plan'}</span>
                        </button>
                    </div>

                    <!-- Clean Empty State (No fabricated progress, no fabricated tasks, no overdue warnings) -->
                    <div class="border border-dashed border-[#D8C7B5] rounded-2xl p-8 sm:p-10 text-center bg-white/50 space-y-3.5 flex flex-col items-center justify-center my-2">
                        <div class="w-12 h-12 rounded-2xl bg-[#F7EFE6] text-[#A6753A] flex items-center justify-center text-2xl shadow-2xs">
                            📋
                        </div>
                        <div class="space-y-1.5 max-w-md">
                            <h4 class="font-heading font-extrabold text-base sm:text-lg text-[#484541]">
                                ${isViLocale() ? 'Bạn chưa có Kế hoạch làm việc' : 'No Working Plan yet'}
                            </h4>
                            <p class="text-xs sm:text-sm text-[#7B7672] leading-relaxed">
                                ${isViLocale() 
                                    ? 'Khi có nhiều deadline hoặc việc cần hoàn thành, bạn có thể tạo Kế hoạch làm việc để phân bổ các bước thực hiện nhẹ nhàng.' 
                                    : 'When you have deadlines or multiple tasks to organize, create a Working Plan to pace your schedule step by step.'}
                            </p>
                        </div>
                        <div class="pt-1.5">
                            <button type="button"
                                    onclick="if (window.TempoRecoverySetup && typeof window.TempoRecoverySetup.promptCreatePlan === 'function') { window.TempoRecoverySetup.promptCreatePlan(); } else if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') { window.TempoApp.navigateTo('plan-workspace'); } else { window.location.hash = '#plan-workspace'; }"
                                    class="px-5 py-2.5 rounded-xl font-bold text-xs sm:text-sm bg-[#D79277] hover:bg-[#C68166] text-white shadow-xs transition cursor-pointer">
                                ${isViLocale() ? 'Tạo Kế hoạch làm việc →' : 'Create a Working Plan →'}
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }

        const totalCount = allItems.length;
        const completedTasks = allItems.filter(item => item.completed);
        const incompleteTasks = allItems.filter(item => !item.completed);
        const completedCount = completedTasks.length;
        const progressPercent = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0;

        // Register all rendered items in map so every single card is guaranteed accessible by ID
        renderedRmodeTasksMap.clear();
        allItems.forEach((item, idx) => {
            renderedRmodeTasksMap.set(String(item.id), item);
            renderedRmodeTasksMap.set(String(idx), item);
            if (item.task && item.task.id) {
                renderedRmodeTasksMap.set(String(item.task.id), item);
            }
        });

        function renderTaskCard(item) {
            const isDone = !!item.completed;
            const safeId = escapeHTML(item.id);
            return `
                <div class="space-y-1.5 recovery-task-card-group" data-task-id="${safeId}">
                    <div class="text-xs font-bold text-[#55504A] cursor-pointer hover:text-[#D79277] transition select-none inline-block"
                         onclick="window.TempoMode.openRmodeTaskDetailModal('${safeId}')"
                         title="View task details for ${escapeHTML(item.name)}">
                        ${escapeHTML(item.timeHeader)}
                    </div>
                    <div onclick="if (!event.target.closest('button[data-task-toggle]')) { window.TempoMode.openRmodeTaskDetailModal('${safeId}'); }"
                         role="button"
                         tabindex="0"
                         aria-label="View task details for ${escapeHTML(item.name)}"
                         onkeydown="if(event.key==='Enter'||event.key===' ') { event.preventDefault(); window.TempoMode.openRmodeTaskDetailModal('${safeId}'); }"
                         class="border border-[#D8C7B5] rounded-2xl p-4 bg-white hover:bg-stone-50/70 hover:border-[#D79277]/60 hover:shadow-xs transition flex items-start space-x-3 group cursor-pointer ${isDone ? 'opacity-85' : ''}">
                        <button type="button" 
                                data-task-toggle="true"
                                onclick="event.stopPropagation(); window.TempoMode.toggleTaskCompletion('${safeId}')"
                                class="w-5 h-5 rounded border ${isDone ? 'bg-[#7B9688] border-[#7B9688] text-white' : 'border-[#C8B39E] bg-white hover:border-[#D79277]'} flex items-center justify-center shrink-0 mt-0.5 cursor-pointer transition select-none"
                                title="${isDone ? 'Đánh dấu chưa xong' : 'Đánh dấu hoàn thành'}">
                            ${isDone ? '✓' : ''}
                        </button>
                        <div class="flex-1 min-w-0 pointer-events-auto">
                            <div class="flex items-center justify-between gap-2">
                                <h5 class="text-base font-extrabold truncate ${isDone ? 'line-through opacity-60 text-stone-400' : 'text-[#484541]'}">
                                    ${escapeHTML(item.name)}
                                </h5>
                                <span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold ${isDone ? 'bg-[#E8EFE8] text-[#556B54]' : item.tagClass} shrink-0">
                                    ${isDone ? (isViLocale() ? 'Đã xong' : 'Done') : escapeHTML(item.tag)}
                                </span>
                            </div>
                            <p class="text-xs text-[#7B7672] mt-1 flex items-center gap-1.5 flex-wrap">
                                <span>${escapeHTML(item.dueDate)}</span>
                                ${item.isOverdue ? `<span class="px-1.5 py-0.2 rounded text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300">${(window.t ? window.t('modes.urgent.overdueBadge') : null) || (isViLocale() ? 'TRỄ DEADLINE' : 'OVERDUE')}</span>` : ''}
                                ${(!item.isOverdue && item.isMissedSchedule) ? `<span class="px-1.5 py-0.2 rounded text-[10px] font-bold bg-stone-100 text-stone-700 border border-stone-300">${isViLocale() ? 'TASK QUÁ LỊCH' : 'MISSED SCHEDULE'}</span>` : ''}
                            </p>
                            <p class="text-xs text-[#7B7672] mt-0.5">
                                ${escapeHTML(item.subtasksText)}
                            </p>
                        </div>
                    </div>
                </div>
            `;
        }

        return `
            <div class="recovery-working-plan-card bg-[#FEFAF4] rounded-3xl p-6 sm:p-7 shadow-xs border border-white/60 space-y-4 max-w-full min-w-0" data-tempo-ui="recovery-working-plan" id="recovery-working-plan">
                <!-- Header -->
                <div class="flex items-center justify-between pb-1 shrink-0">
                    <h3 class="font-heading text-2xl font-extrabold text-[#484541] tracking-tight">
                        <span class="sr-only">${isViLocale() ? 'Kế hoạch làm việc của bạn - ' : 'Your plan for today - '}</span>${isViLocale() ? (window.t ? window.t('modes.urgent.workingPlanTitle', {}, 'Working Plan') : 'Working Plan') : 'Working Plan'}
                    </h3>
                    <button type="button"
                            onclick="if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') { window.TempoApp.navigateTo('plan-workspace'); } else { window.location.hash = '#plan-workspace'; }"
                            class="px-4 py-1.5 rounded-full text-xs font-bold bg-[#D79277] hover:bg-[#C68166] text-white shadow-2xs transition cursor-pointer">
                        <span class="sr-only">${isViLocale() ? 'Xem / Chỉnh sửa kế hoạch - ' : 'View / Edit Plan - '}</span><span>${window.t ? window.t('modes.urgent.editPlan', {}, (isViLocale() ? 'Sửa plan' : 'Edit Plan')) : (isViLocale() ? 'Sửa plan' : 'Edit Plan')}</span>
                    </button>
                </div>

                <!-- Overall Progress Bar -->
                <div class="flex items-center space-x-3 pb-2 shrink-0">
                    <div class="flex-1 h-2 bg-[#E0DDD9] rounded-full overflow-hidden">
                        <div class="h-full bg-[#D79277] rounded-full transition-all duration-300" style="width: ${progressPercent}%;"></div>
                    </div>
                    <span class="text-xs font-semibold text-[#6F6B68] shrink-0">${completedCount}/${totalCount} ${isViLocale() ? 'task' : 'tasks'}</span>
                </div>

                <!-- Two-Column Container (Left: Tasks, Right: Task Done) -->
                <div class="recovery-working-plan-scroll flex-1 min-h-0 overflow-x-auto overflow-y-auto pr-1 pb-1"
                     data-tempo-ui="recovery-plan-scroll-container">
                    <div class="recovery-plan-columns grid flex flex-row items-stretch h-full gap-4 md:gap-5 w-full min-w-0 pt-1"
                         data-tempo-ui="recovery-plan-columns">

                        <!-- Left Column: Tasks (all incomplete tasks) -->
                        <div class="recovery-plan-column flex flex-col h-full min-w-0 flex-1"
                             data-tempo-ui="recovery-date-column"
                             data-tempo-column="tasks">
                            <div class="text-xs sm:text-sm font-extrabold text-[#55504A] uppercase tracking-wider flex items-center justify-between pb-2 shrink-0">
                                <span>${isViLocale() ? 'CÔNG VIỆC' : 'TASKS'}</span>
                                <span class="text-xs font-semibold px-2 py-0.5 rounded-full bg-[#F3EFEA] text-[#7B7672]">(${incompleteTasks.length})</span>
                            </div>
                            <div class="recovery-column-tasks flex-1 min-h-0 overflow-y-auto space-y-4 pr-1.5" data-tempo-ui="recovery-column-task-list">
                                ${incompleteTasks.length > 0 ? incompleteTasks.map(renderTaskCard).join('') : `
                                    <div class="p-4 text-xs text-[#8C8782] italic text-center border border-dashed border-[#D8C7B5] rounded-2xl bg-white/50">
                                        ${isViLocale() ? 'Không có task nào đang chờ' : 'No pending tasks'}
                                    </div>
                                `}
                            </div>
                        </div>

                        <!-- Vertical Divider -->
                        <div class="recovery-plan-divider flex justify-center items-stretch shrink-0 self-stretch px-1" aria-hidden="true">
                            <div class="w-1.5 bg-[#D2D6D8] rounded-full self-stretch my-1"></div>
                        </div>

                        <!-- Right Column: Task Done (all completed tasks) -->
                        <div class="recovery-plan-column flex flex-col h-full min-w-0 flex-1"
                             data-tempo-ui="recovery-done-column"
                             data-tempo-column="done">
                            <div class="text-xs sm:text-sm font-extrabold text-[#7B9688] uppercase tracking-wider flex items-center justify-between pb-2 shrink-0">
                                <span>${isViLocale() ? 'VIỆC ĐÃ XONG' : 'TASK DONE'}</span>
                                <span class="text-xs font-semibold px-2 py-0.5 rounded-full bg-[#EBF1ED] text-[#4A6B5D]">(${completedTasks.length})</span>
                            </div>
                            <div class="recovery-column-tasks flex-1 min-h-0 overflow-y-auto space-y-4 pr-1.5" data-tempo-ui="recovery-column-task-list">
                                ${completedTasks.length > 0 ? completedTasks.map(renderTaskCard).join('') : `
                                    <div class="p-4 text-xs text-[#8C8782] italic text-center border border-dashed border-[#D8C7B5] rounded-2xl bg-white/50">
                                        ${isViLocale() ? 'Công việc đã hoàn thành sẽ xuất hiện tại đây' : 'Completed tasks will appear here'}
                                    </div>
                                `}
                            </div>
                        </div>

                    </div>
                </div>
            </div>
        `;
    }


    // =========================================================================
    // RMODE TASK DETAIL POPUP MODAL (REUSING WORKPLAN TASK DETAIL UI & ACTIONS)
    // =========================================================================

    let activeRmodeDetailTaskId = null;
    let isRmodeDetailEditingTitle = false;
    let isRmodeDetailEditingDeadline = false;
    let isRmodeDetailEditingNote = false;
    let isRmodeDetailLabelMenuOpen = false;
    let isRmodeDetailAddingSubtask = false;
    let editingRmodeSubtaskId = null;

    // Shared map storing every rendered task card from the active dashboard view
    const renderedRmodeTasksMap = new Map();

    function formatRmodeDeadline(dateStr, timeStr) {
        if (window.TempoI18n && typeof window.TempoI18n.formatDeadline === 'function') {
            return window.TempoI18n.formatDeadline(dateStr, timeStr);
        }
        if (!dateStr || dateStr === 'No fixed deadline') return 'No fixed deadline';
        if (dateStr.includes(' ') && !timeStr) {
            const parts = dateStr.split(' ');
            dateStr = parts[0];
            timeStr = parts[1];
        }
        try {
            const [y, m, d] = dateStr.split('-').map(Number);
            if (!y || !m || !d) return dateStr;
            const date = new Date(y, m - 1, d);
            const monthDay = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
            if (timeStr) {
                let [h, min] = timeStr.split(':').map(Number);
                const ampm = h >= 12 ? 'PM' : 'AM';
                h = h % 12 || 12;
                const minStr = String(min).padStart(2, '0');
                return `${monthDay} - ${h}:${minStr} ${ampm}`;
            }
            return monthDay;
        } catch (e) {
            return dateStr;
        }
    }

    function getRmodeActivePlan() {
        let plan = null;
        if (window.TempoPlanWorkspace && typeof window.TempoPlanWorkspace.getActivePlan === 'function') {
            plan = window.TempoPlanWorkspace.getActivePlan();
        }
        if (!plan && window.TempoPlanStore && typeof window.TempoPlanStore.getActivePlan === 'function') {
            plan = window.TempoPlanStore.getActivePlan('recovery') || window.TempoPlanStore.getActivePlan('emergency');
        }
        if (!plan && window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.getConfirmedPlan === 'function') {
            plan = window.TempoEmergencyFlow.getConfirmedPlan();
        }
        if (!plan) {
            try {
                const key = getWorkingPlanStorageKey();
                const saved = localStorage.getItem(key);
                if (saved) plan = JSON.parse(saved);
            } catch (e) {}
        }
        if (plan) {
            const currentUserId = (window.TempoAuth && typeof window.TempoAuth.getCurrentUserId === 'function') 
                ? window.TempoAuth.getCurrentUserId() : null;
            if (currentUserId) {
                if (plan.userId && plan.userId !== currentUserId) return null;
                if (plan.user_id && plan.user_id !== currentUserId) return null;
                if (!plan.userId && !plan.user_id) return null;
            }
            if (!Array.isArray(plan.plannedTasks)) plan.plannedTasks = [];
            if (!Array.isArray(plan.unarrangedTasks)) plan.unarrangedTasks = [];
            if (!Array.isArray(plan.tasks)) plan.tasks = [];
        }
        return plan;
    }

    function getRmodeTaskData(taskId) {
        if (!taskId) return null;
        const sTaskId = String(taskId);
        const plan = getRmodeActivePlan();
        let matchedTask = null;
        let matchedPlanItem = null;
        const renderedItem = renderedRmodeTasksMap.get(sTaskId);

        // 1. Direct match from currently rendered task cards map
        if (renderedItem) {
            matchedTask = renderedItem.task || renderedItem;
            matchedPlanItem = renderedItem;
        }

        // 2. Search plan collections across all possible ID fields
        if (plan) {
            if (Array.isArray(plan.plannedTasks)) {
                for (const pt of plan.plannedTasks) {
                    const t = pt.task || pt;
                    if (t && (String(t.id) === sTaskId || String(pt.id) === sTaskId || String(pt.taskId) === sTaskId)) {
                        matchedTask = t;
                        matchedPlanItem = pt;
                        break;
                    }
                }
            }
            if (!matchedTask && Array.isArray(plan.unarrangedTasks)) {
                for (const u of plan.unarrangedTasks) {
                    const t = u.task || u;
                    if (t && (String(t.id) === sTaskId || String(u.id) === sTaskId)) {
                        matchedTask = t;
                        matchedPlanItem = u;
                        break;
                    }
                }
            }
            if (!matchedTask && Array.isArray(plan.unallocatedTasks)) {
                for (const u of plan.unallocatedTasks) {
                    const t = u.task || u;
                    if (t && (String(t.id) === sTaskId || String(u.id) === sTaskId)) {
                        matchedTask = t;
                        matchedPlanItem = u;
                        break;
                    }
                }
            }
            if (!matchedTask && Array.isArray(plan.tasks)) {
                for (const t of plan.tasks) {
                    if (t && String(t.id) === sTaskId) {
                        matchedTask = t;
                        break;
                    }
                }
            }
            if (!matchedTask && Array.isArray(plan.completedTasks)) {
                for (const c of plan.completedTasks) {
                    const t = c.task || c;
                    if (t && (String(t.id) === sTaskId || String(c.id) === sTaskId)) {
                        matchedTask = t;
                        matchedPlanItem = c;
                        break;
                    }
                }
            }
            if (!matchedTask && Array.isArray(plan.doneTasks)) {
                for (const d of plan.doneTasks) {
                    const t = d.task || d;
                    if (t && (String(t.id) === sTaskId || String(d.id) === sTaskId)) {
                        matchedTask = t;
                        matchedPlanItem = d;
                        break;
                    }
                }
            }
        }

        // 3. Fallback definitions for canonical mock tasks
        if (!matchedTask) {
            const mockMap = {
                'rmode-mock-1': 'task-marketing-research',
                'rmode-mock-2': 'task-event-proposal',
                'rmode-mock-3': 'task-edit-video'
            };
            const canonicalId = mockMap[sTaskId] || sTaskId;
            if (canonicalId === 'task-marketing-research') {
                matchedTask = {
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
                    timeHeader: 'Hôm nay, 14:00 đến 16:00',
                    userLabel: 'Now',
                    description: 'Create a sheet to manage references',
                    subtasks: [
                        { id: 'sub-1', title: 'Subtask 1: Outline', completed: false, durationMinutes: 30 },
                        { id: 'sub-2', title: 'Subtask 2: Literature Review', completed: false, durationMinutes: 45 },
                        { id: 'sub-3', title: 'Subtask 3: Research Gap', completed: false, durationMinutes: 30 },
                        { id: 'sub-4', title: 'Subtask 4: Methodology', completed: false, durationMinutes: 20 },
                        { id: 'sub-5', title: 'Subtask 5: Data Analysis', completed: false, durationMinutes: 15 },
                        { id: 'sub-6', title: 'Subtask 6: Summary Report', completed: false, durationMinutes: 10 }
                    ]
                };
            } else if (canonicalId === 'task-event-proposal') {
                matchedTask = {
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
                    timeHeader: 'Hôm nay, 17:00 đến 19:00',
                    userLabel: 'Then',
                    description: 'Coordinate with design team for event collateral',
                    subtasks: [
                        { id: 'sub-ep-1', title: 'Subtask 1: Budget Draft', completed: false, durationMinutes: 45 },
                        { id: 'sub-ep-2', title: 'Subtask 2: Venue Options', completed: false, durationMinutes: 60 },
                        { id: 'sub-ep-3', title: 'Subtask 3: Guest List', completed: false, durationMinutes: 45 }
                    ]
                };
            } else if (canonicalId === 'task-edit-video') {
                matchedTask = {
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
                    timeHeader: 'Tomorrow, 1:00 PM to 5:00 PM',
                    userLabel: 'Later',
                    description: 'Export in 1080p format for social channels',
                    subtasks: []
                };
            }
        }

        // 4. Construct complete task from rendered item if still missing
        if (!matchedTask && renderedItem) {
            matchedTask = {
                id: sTaskId,
                name: renderedItem.name || 'Untitled Task',
                completed: !!renderedItem.completed,
                deadlineDate: renderedItem.date || '',
                timeHeader: renderedItem.timeHeader || '',
                userLabel: renderedItem.tag || 'Later',
                subtasks: [],
                description: ''
            };
        }

        // 5. Ensure critical properties exist
        if (matchedTask) {
            if (!matchedTask.id) matchedTask.id = sTaskId;
            if (!matchedTask.name) matchedTask.name = (renderedItem && renderedItem.name) ? renderedItem.name : 'Untitled Task';
            if (!Array.isArray(matchedTask.subtasks)) matchedTask.subtasks = [];
            if (!matchedTask.timeHeader && renderedItem && renderedItem.timeHeader) {
                matchedTask.timeHeader = renderedItem.timeHeader;
            }
            if (!matchedTask.userLabel && renderedItem && renderedItem.tag) {
                matchedTask.userLabel = renderedItem.tag;
            }
            try {
                const mockTasks = JSON.parse(localStorage.getItem(getRmodeMockTasksKey()) || '{}');
                if (typeof mockTasks[matchedTask.id] === 'boolean') {
                    matchedTask.completed = mockTasks[matchedTask.id];
                } else if (typeof mockTasks[sTaskId] === 'boolean') {
                    matchedTask.completed = mockTasks[sTaskId];
                }
            } catch (e) {}
        }

        return { plan, task: matchedTask, plannedItem: matchedPlanItem || renderedItem };
    }

    function persistRmodePlanData(plan, task) {
        if (task) {
            // Update in-memory map
            if (renderedRmodeTasksMap.has(String(task.id))) {
                const item = renderedRmodeTasksMap.get(String(task.id));
                if (item) {
                    item.task = task;
                    item.name = task.name || item.name;
                    item.completed = !!task.completed;
                    if (task.deadlineDate) {
                        item.dueDate = `Deadline: ${formatPlanDateHeader(task.deadlineDate, task.deadlineDate)}`;
                    }
                    if (Array.isArray(task.subtasks)) {
                        const doneCount = task.subtasks.filter(s => s && s.completed).length;
                        item.subtasksText = `${doneCount}/${task.subtasks.length} subtasks`;
                    }
                }
            }
        }

        if (plan) {
            if (task) {
                let found = false;
                if (Array.isArray(plan.plannedTasks)) {
                    for (const pt of plan.plannedTasks) {
                        const t = pt.task || pt;
                        if (t && (String(t.id) === String(task.id) || String(pt.id) === String(task.id))) {
                            found = true;
                            if (pt.task) Object.assign(pt.task, task);
                            else Object.assign(pt, task);
                            break;
                        }
                    }
                }
                if (!found && Array.isArray(plan.unarrangedTasks)) {
                    for (const u of plan.unarrangedTasks) {
                        const t = u.task || u;
                        if (t && (String(t.id) === String(task.id) || String(u.id) === String(task.id))) {
                            found = true;
                            if (u.task) Object.assign(u.task, task);
                            else Object.assign(u, task);
                            break;
                        }
                    }
                }
                if (!found && Array.isArray(plan.tasks)) {
                    for (const t of plan.tasks) {
                        if (t && String(t.id) === String(task.id)) {
                            found = true;
                            Object.assign(t, task);
                            break;
                        }
                    }
                }
                if (!found) {
                    if (!Array.isArray(plan.plannedTasks)) plan.plannedTasks = [];
                    plan.plannedTasks.push({
                        dayDate: task.deadlineDate || getLocalTodayISO(),
                        dayLabel: 'Hôm nay',
                        startTime: '2:00 PM',
                        endTime: '4:00 PM',
                        executionBadge: task.userLabel || 'Now',
                        task: task
                    });
                }
            }

            try {
                localStorage.setItem(getWorkingPlanStorageKey(), JSON.stringify(plan));
                const currentUserId = (window.TempoAuth && typeof window.TempoAuth.getCurrentUserId === 'function') ? window.TempoAuth.getCurrentUserId() : null;
                if (!currentUserId) {
                    localStorage.setItem('tempo_working_plan', JSON.stringify(plan));
                }
            } catch (e) {}

            if (window.TempoPlanStore && typeof window.TempoPlanStore.saveActivePlan === 'function') {
                window.TempoPlanStore.saveActivePlan('emergency', plan);
                window.TempoPlanStore.saveActivePlan('recovery', plan);
            }
            if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.setConfirmedPlan === 'function') {
                window.TempoEmergencyFlow.setConfirmedPlan(plan);
            }
        }

        // Also sync tempo_rmode_mock_tasks if applicable
        if (task) {
            try {
                let mockTasks = JSON.parse(localStorage.getItem(getRmodeMockTasksKey()) || '{}');
                mockTasks[task.id] = !!task.completed;
                const mockMap = {
                    'task-marketing-research': 'rmode-mock-1',
                    'task-event-proposal': 'rmode-mock-2',
                    'task-edit-video': 'rmode-mock-3'
                };
                if (mockMap[task.id]) {
                    mockTasks[mockMap[task.id]] = !!task.completed;
                }
                localStorage.setItem(getRmodeMockTasksKey(), JSON.stringify(mockTasks));
            } catch (e) {}
        }

        renderRmodeHome();
        if (typeof renderActiveModeHome === 'function') {
            renderActiveModeHome();
        }
        if (window.TempoPlanWorkspace && typeof window.TempoPlanWorkspace.render === 'function') {
            window.TempoPlanWorkspace.render();
        }
    }

    function openRmodeTaskDetailModal(taskId) {
        activeRmodeDetailTaskId = taskId;
        isRmodeDetailEditingTitle = false;
        isRmodeDetailEditingDeadline = false;
        isRmodeDetailEditingNote = false;
        isRmodeDetailLabelMenuOpen = false;
        isRmodeDetailAddingSubtask = false;
        editingRmodeSubtaskId = null;
        renderRmodeTaskDetailModalDOM();
    }

    function closeRmodeTaskDetailModal() {
        activeRmodeDetailTaskId = null;
        isRmodeDetailEditingTitle = false;
        isRmodeDetailEditingDeadline = false;
        isRmodeDetailEditingNote = false;
        isRmodeDetailLabelMenuOpen = false;
        isRmodeDetailAddingSubtask = false;
        editingRmodeSubtaskId = null;
        renderRmodeTaskDetailModalDOM();
    }

    function isRmodeTaskDetailModalOpen() {
        return Boolean(activeRmodeDetailTaskId);
    }

    function renderRmodeTaskDetailModalDOM() {
        const root = document.getElementById('rmode-task-modal-root');
        if (root) {
            root.innerHTML = renderRmodeTaskDetailModalHTML();
        }
    }

    function toggleRmodeDetailTitleEdit() {
        isRmodeDetailEditingTitle = !isRmodeDetailEditingTitle;
        renderRmodeTaskDetailModalDOM();
        if (isRmodeDetailEditingTitle) {
            setTimeout(() => {
                const input = document.getElementById('rmode-edit-title-input');
                if (input) {
                    input.focus();
                    input.select();
                }
            }, 50);
        }
    }

    function saveRmodeDetailTitleEdit(taskId) {
        const input = document.getElementById('rmode-edit-title-input');
        const newTitle = input ? input.value.trim() : '';
        if (!newTitle) return;

        const taskInfo = getRmodeTaskData(taskId);
        if (!taskInfo || !taskInfo.task) return;

        taskInfo.task.name = newTitle;
        taskInfo.task.title = newTitle;
        if (taskInfo.plannedItem && taskInfo.plannedItem.task) {
            taskInfo.plannedItem.task.name = newTitle;
            taskInfo.plannedItem.task.title = newTitle;
        }

        isRmodeDetailEditingTitle = false;
        persistRmodePlanData(taskInfo.plan, taskInfo.task);
        renderRmodeTaskDetailModalDOM();
    }

    function toggleRmodeDetailDeadlineEdit() {
        isRmodeDetailEditingDeadline = !isRmodeDetailEditingDeadline;
        renderRmodeTaskDetailModalDOM();
    }

    function saveRmodeDetailDeadlineEdit(taskId) {
        const dateInput = document.getElementById('rmode-edit-deadline-date');
        const timeInput = document.getElementById('rmode-edit-deadline-time');
        const noDeadlineInput = document.getElementById('rmode-edit-no-deadline');

        const noDeadline = noDeadlineInput ? noDeadlineInput.checked : false;
        const date = dateInput ? dateInput.value : '';
        const time = timeInput ? timeInput.value : '';

        const taskInfo = getRmodeTaskData(taskId);
        if (!taskInfo || !taskInfo.task) return;

        if (noDeadline) {
            taskInfo.task.hasDeadline = false;
            taskInfo.task.deadlineDate = '';
            taskInfo.task.deadlineTime = '';
            taskInfo.task.deadline = 'No fixed deadline';
        } else {
            taskInfo.task.hasDeadline = true;
            taskInfo.task.deadlineDate = date;
            taskInfo.task.deadlineTime = time || taskInfo.task.deadlineTime || '';
            taskInfo.task.deadline = taskInfo.task.deadlineTime ? `${date} ${taskInfo.task.deadlineTime}` : date;
        }

        delete taskInfo.task.isOverdue;
        taskInfo.task.isOverdue = false;

        if (taskInfo.plannedItem && taskInfo.plannedItem.task) {
            taskInfo.plannedItem.task.hasDeadline = taskInfo.task.hasDeadline;
            taskInfo.plannedItem.task.deadlineDate = taskInfo.task.deadlineDate;
            taskInfo.plannedItem.task.deadlineTime = taskInfo.task.deadlineTime;
            taskInfo.plannedItem.task.deadline = taskInfo.task.deadline;
            delete taskInfo.plannedItem.task.isOverdue;
            taskInfo.plannedItem.task.isOverdue = false;
        }

        isRmodeDetailEditingDeadline = false;
        persistRmodePlanData(taskInfo.plan, taskInfo.task);
        renderRmodeTaskDetailModalDOM();
    }

    function toggleRmodeDetailNoteEdit() {
        isRmodeDetailEditingNote = !isRmodeDetailEditingNote;
        renderRmodeTaskDetailModalDOM();
        if (isRmodeDetailEditingNote) {
            setTimeout(() => {
                const textarea = document.getElementById('rmode-note-editor-text');
                if (textarea) {
                    textarea.focus();
                    textarea.select();
                }
            }, 50);
        }
    }

    function saveRmodeDetailNote(taskId) {
        const input = document.getElementById('rmode-note-editor-text');
        const text = input ? input.value.trim() : '';
        const taskInfo = getRmodeTaskData(taskId);
        if (!taskInfo || !taskInfo.task) return;

        taskInfo.task.note = text;
        taskInfo.task.description = text;
        if (taskInfo.plannedItem && taskInfo.plannedItem.task) {
            taskInfo.plannedItem.task.note = text;
            taskInfo.plannedItem.task.description = text;
        }

        if (window.TempoToolNotes && typeof window.TempoToolNotes.saveTaskNote === 'function') {
            window.TempoToolNotes.saveTaskNote(taskId, taskInfo.task.name || 'Task', text);
        }

        isRmodeDetailEditingNote = false;
        persistRmodePlanData(taskInfo.plan, taskInfo.task);
        renderRmodeTaskDetailModalDOM();
    }

    function deleteRmodeDetailNote(taskId) {
        const taskInfo = getRmodeTaskData(taskId);
        if (!taskInfo || !taskInfo.task) return;

        taskInfo.task.note = '';
        taskInfo.task.description = '';
        if (taskInfo.plannedItem && taskInfo.plannedItem.task) {
            taskInfo.plannedItem.task.note = '';
            taskInfo.plannedItem.task.description = '';
        }

        if (window.TempoToolNotes && typeof window.TempoToolNotes.deleteTaskNote === 'function') {
            window.TempoToolNotes.deleteTaskNote(taskId);
        }

        isRmodeDetailEditingNote = false;
        persistRmodePlanData(taskInfo.plan, taskInfo.task);
        renderRmodeTaskDetailModalDOM();
    }

    function toggleRmodeDetailTaskComplete(taskId) {
        const taskInfo = getRmodeTaskData(taskId);
        if (!taskInfo || !taskInfo.task) return;

        const newCompleted = !taskInfo.task.completed;
        taskInfo.task.completed = newCompleted;
        setTaskCompletionStatus(taskId, newCompleted);
        renderRmodeTaskDetailModalDOM();
    }

    function toggleRmodeDetailSubtask(taskId, subtaskId) {
        const taskInfo = getRmodeTaskData(taskId);
        if (!taskInfo || !taskInfo.task) return;
        if (!Array.isArray(taskInfo.task.subtasks)) taskInfo.task.subtasks = [];

        const sub = taskInfo.task.subtasks.find(s => String(s.id) === String(subtaskId));
        if (sub) {
            sub.completed = !sub.completed;
            persistRmodePlanData(taskInfo.plan, taskInfo.task);
            renderRmodeTaskDetailModalDOM();
        }
    }

    function toggleRmodeDetailAddSubtask() {
        isRmodeDetailAddingSubtask = !isRmodeDetailAddingSubtask;
        renderRmodeTaskDetailModalDOM();
        if (isRmodeDetailAddingSubtask) {
            setTimeout(() => {
                const input = document.getElementById('rmode-new-subtask-title');
                if (input) input.focus();
            }, 50);
        }
    }

    function addRmodeDetailSubtask(taskId) {
        const input = document.getElementById('rmode-new-subtask-title');
        const title = input ? input.value.trim() : '';
        if (!title) return;

        const taskInfo = getRmodeTaskData(taskId);
        if (!taskInfo || !taskInfo.task) return;
        if (!Array.isArray(taskInfo.task.subtasks)) taskInfo.task.subtasks = [];

        taskInfo.task.subtasks.push({
            id: 'sub_' + Date.now(),
            title: title,
            durationMinutes: 15,
            completed: false
        });

        isRmodeDetailAddingSubtask = false;
        persistRmodePlanData(taskInfo.plan, taskInfo.task);
        renderRmodeTaskDetailModalDOM();
    }

    function removeRmodeDetailSubtask(taskId, subtaskId) {
        const taskInfo = getRmodeTaskData(taskId);
        if (!taskInfo || !taskInfo.task || !Array.isArray(taskInfo.task.subtasks)) return;

        taskInfo.task.subtasks = taskInfo.task.subtasks.filter(s => String(s.id) !== String(subtaskId));
        persistRmodePlanData(taskInfo.plan, taskInfo.task);
        renderRmodeTaskDetailModalDOM();
    }

    function toggleRmodeDetailSubtaskEdit(subtaskId) {
        editingRmodeSubtaskId = subtaskId;
        renderRmodeTaskDetailModalDOM();
        if (subtaskId) {
            setTimeout(() => {
                const input = document.getElementById(`rmode-edit-subtask-input-${subtaskId}`);
                if (input) {
                    input.focus();
                    input.select();
                }
            }, 50);
        }
    }

    function saveRmodeDetailSubtaskTitle(taskId, subtaskId) {
        const input = document.getElementById(`rmode-edit-subtask-input-${subtaskId}`);
        const newTitle = input ? input.value.trim() : '';
        if (!newTitle) return;

        const taskInfo = getRmodeTaskData(taskId);
        if (!taskInfo || !taskInfo.task || !Array.isArray(taskInfo.task.subtasks)) return;

        const sub = taskInfo.task.subtasks.find(s => String(s.id) === String(subtaskId));
        if (sub) {
            sub.title = newTitle;
            editingRmodeSubtaskId = null;
            persistRmodePlanData(taskInfo.plan, taskInfo.task);
            renderRmodeTaskDetailModalDOM();
        }
    }

    function toggleRmodeDetailLabelMenu() {
        isRmodeDetailLabelMenuOpen = !isRmodeDetailLabelMenuOpen;
        renderRmodeTaskDetailModalDOM();
    }

    function setRmodeDetailTaskLabel(taskId, newLabel) {
        isRmodeDetailLabelMenuOpen = false;
        const taskInfo = getRmodeTaskData(taskId);
        if (!taskInfo || !taskInfo.task) return;

        taskInfo.task.userLabel = newLabel;
        taskInfo.task.priorityCategory = (newLabel === 'Now') ? 'DO_FIRST' : 'LATER';
        if (taskInfo.plannedItem) {
            taskInfo.plannedItem.executionBadge = newLabel;
        }

        persistRmodePlanData(taskInfo.plan, taskInfo.task);
        renderRmodeTaskDetailModalDOM();
    }

    function promptClearRmodeTask(taskId) {
        if (!confirm('Bạn có chắc chắn muốn xóa task này khỏi kế hoạch không?')) return;
        const taskInfo = getRmodeTaskData(taskId);
        if (!taskInfo || !taskInfo.plan) {
            closeRmodeTaskDetailModal();
            return;
        }

        const plan = taskInfo.plan;
        if (Array.isArray(plan.plannedTasks)) {
            plan.plannedTasks = plan.plannedTasks.filter(item => {
                const t = item.task || item;
                return t && String(t.id) !== String(taskId);
            });
        }
        if (Array.isArray(plan.unarrangedTasks)) {
            plan.unarrangedTasks = plan.unarrangedTasks.filter(item => {
                const t = item.task || item;
                return t && String(t.id) !== String(taskId);
            });
        }
        if (Array.isArray(plan.tasks)) {
            plan.tasks = plan.tasks.filter(t => t && String(t.id) !== String(taskId));
        }

        closeRmodeTaskDetailModal();
        persistRmodePlanData(plan);
        if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
            window.TempoApp.showToast('Task removed from working plan.');
        }
    }

    function handleRmodeTaskFocus(taskId) {
        closeRmodeTaskDetailModal();
        startTaskFocus(taskId);
    }

    function handleRmodeTaskReschedule(taskId) {
        closeRmodeTaskDetailModal();
        if (window.TempoPlanWorkspace && typeof window.TempoPlanWorkspace.openRescheduleModal === 'function') {
            window.TempoPlanWorkspace.openRescheduleModal(taskId);
        }
        if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
            window.TempoApp.navigateTo('tool-workplan', taskId);
        } else {
            window.location.hash = '#tool-workplan';
        }
    }

    function renderRmodeTaskDetailModalHTML() {
        if (!activeRmodeDetailTaskId) return '';

        const taskInfo = getRmodeTaskData(activeRmodeDetailTaskId);
        if (!taskInfo || !taskInfo.task) return '';

        const task = taskInfo.task;
        const plannedItem = taskInfo.plannedItem;
        const isDone = !!task.completed;

        // Schedule string
        let detailScheduleStr = isViLocale() ? `Lịch linh hoạt • ~${task.durationLabel || '1h'}` : `Flexible schedule • ~${task.durationLabel || '1h'}`;
        const itemDayDate = (plannedItem && plannedItem.dayDate) || task.dayDate || task._dayDate;
        const itemSchedLabel = itemDayDate ? formatScheduledDateLabel(itemDayDate, isViLocale()) : '';
        if (plannedItem && plannedItem.timeHeader) {
            detailScheduleStr = plannedItem.timeHeader;
        } else if (plannedItem && plannedItem.startTime && plannedItem.endTime) {
            detailScheduleStr = `${itemSchedLabel || formatScheduledDateLabel(getLocalTodayISO(), isViLocale())}, ${formatTime12H(plannedItem.startTime)} to ${formatTime12H(plannedItem.endTime)}`;
        } else if (itemSchedLabel) {
            detailScheduleStr = `${itemSchedLabel}, ${isViLocale() ? 'Đã lên lịch' : 'Scheduled'}`;
        } else if (task.timeHeader) {
            detailScheduleStr = task.timeHeader;
        } else if (task.deadlineDate) {
            detailScheduleStr = `Deadline: ${formatPlanDateHeader(task.deadlineDate, task.deadlineDate)}`;
        }

        // Priority Badge (dynamically evaluated from task or plannedItem)
        let priorityBadge = 'Later';
        if (task.userLabel === 'Now' || (plannedItem && (plannedItem.tag === 'Now' || plannedItem.executionBadge === 'Now'))) {
            priorityBadge = 'Now';
        } else if (task.userLabel === 'Then' || (plannedItem && (plannedItem.tag === 'Then' || plannedItem.executionBadge === 'Then'))) {
            priorityBadge = 'Then';
        }

        // Subtasks calculations
        const subtasks = Array.isArray(task.subtasks) ? task.subtasks : [];
        const totalSubtasks = subtasks.length;
        const completedSubtasks = subtasks.filter(s => s && s.completed).length;

        // Note / Description
        const noteText = (task.note || task.description || (window.TempoToolNotes && window.TempoToolNotes.getTaskNote ? window.TempoToolNotes.getTaskNote(task.id) : '') || '').trim();

        return `
            <div id="rmode-task-detail-modal" 
                 class="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-stone-900/50 backdrop-blur-xs transition-all duration-150"
                 onclick="if(event.target === this) window.TempoMode.closeRmodeTaskDetailModal();"
                 role="dialog"
                 aria-modal="true"
                 aria-labelledby="rmode-task-modal-title">
                
                <div class="bg-[#FDFBF6] border border-[#E3C7A5] rounded-3xl p-6 sm:p-7 max-w-lg w-full max-h-[90vh] overflow-y-auto space-y-4 shadow-xl relative text-left"
                     onclick="event.stopPropagation();">
                    
                    <!-- Close Button (✕) -->
                    <button type="button" 
                            onclick="window.TempoMode.closeRmodeTaskDetailModal()"
                            class="absolute top-5 right-5 w-8 h-8 rounded-full bg-[#F3EDE2] hover:bg-[#EAE0D1] text-[#6B5E51] hover:text-[#2D2823] flex items-center justify-center text-sm font-bold transition cursor-pointer"
                            aria-label="${isViLocale() ? 'Đóng chi tiết task' : 'Close task detail'}">
                        ✕
                    </button>

                    <!-- Schedule Header -->
                    <div class="text-xs sm:text-sm font-bold text-[#D9A18B] tracking-wide pr-8">
                        ${escapeHTML(detailScheduleStr)}
                    </div>

                    <!-- Title and Priority Badge Row -->
                    <div class="flex items-center justify-between gap-3 pb-1">
                        <div class="flex-1 min-w-0 pr-2">
                            ${isRmodeDetailEditingTitle ? `
                                <div class="flex items-center gap-2">
                                    <input id="rmode-edit-title-input" 
                                           type="text" 
                                           value="${escapeHTML(task.name || '')}" 
                                           class="w-full px-3 py-1.5 text-base font-bold text-[#202124] border border-[#D99E87] rounded-xl bg-white focus:outline-hidden focus:ring-2 focus:ring-[#D99E87]"
                                           onkeydown="if(event.key==='Enter') window.TempoMode.saveRmodeDetailTitleEdit('${task.id}'); if(event.key==='Escape') window.TempoMode.toggleRmodeDetailTitleEdit();" />
                                    <button type="button" 
                                            onclick="window.TempoMode.saveRmodeDetailTitleEdit('${task.id}')"
                                            class="px-3 py-1.5 bg-[#D99E87] text-white rounded-xl text-xs font-bold hover:bg-[#C98E77] cursor-pointer">
                                        Save
                                    </button>
                                    <button type="button" 
                                            onclick="window.TempoMode.toggleRmodeDetailTitleEdit()"
                                            class="px-2.5 py-1.5 border border-stone-300 text-stone-600 rounded-xl text-xs font-bold hover:bg-stone-100 cursor-pointer">
                                        Cancel
                                    </button>
                                </div>
                            ` : `
                                <div class="flex items-center gap-2 group">
                                    <h2 id="rmode-task-modal-title" class="font-heading text-xl sm:text-2xl font-bold text-[#202124] truncate ${isDone ? 'line-through text-stone-400' : ''}">
                                        ${escapeHTML(task.name || 'Untitled Task')}
                                    </h2>
                                    <button type="button" 
                                            onclick="window.TempoMode.toggleRmodeDetailTitleEdit()" 
                                            class="text-[#D99E87] hover:text-[#C98E77] text-xs font-semibold p-1 hover:bg-[#F3EDE2] rounded-md transition cursor-pointer" 
                                            title="${isViLocale() ? 'Chỉnh sửa tên task' : 'Edit task name'}">
                                        ✎
                                    </button>
                                </div>
                            `}
                        </div>

                        <!-- Priority Badge with Dropdown -->
                        <div class="relative inline-block shrink-0">
                            <button type="button"
                                    ${isDone ? '' : `onclick="event.stopPropagation(); window.TempoMode.toggleRmodeDetailLabelMenu();"`}
                                    class="px-3 py-0.5 rounded-full text-xs font-bold ${isDone ? 'bg-[#92A491] text-white' : (priorityBadge === 'Now' ? 'bg-[#D99E87] text-white' : (priorityBadge === 'Then' ? 'bg-[#F7E7D4] text-[#A6753A]' : 'bg-[#E8ECF1] text-[#7B96A6]'))} shrink-0 ${!isDone ? 'cursor-pointer hover:opacity-90 transition flex items-center space-x-1' : ''}"
                                    title="${isDone ? 'Completed task' : 'Change priority'}">
                                <span>${isDone ? (isViLocale() ? 'Hoàn thành' : 'Done') : (priorityBadge === 'Now' ? (isViLocale() ? 'Làm ngay' : 'Now') : (priorityBadge === 'Then' ? (isViLocale() ? 'Sau đó' : 'Then') : (priorityBadge === 'Later' ? (isViLocale() ? 'Để sau' : 'Later') : priorityBadge)))}</span>
                                ${!isDone ? '<span class="text-[9px] opacity-75">▾</span>' : ''}
                            </button>
                            ${isRmodeDetailLabelMenuOpen && !isDone ? `
                                <div class="absolute right-0 top-full mt-1 z-30 bg-white border border-[#E3C7A5] rounded-xl shadow-lg py-1 w-28 text-xs font-semibold overflow-hidden"
                                     onclick="event.stopPropagation();">
                                    <button type="button"
                                            onclick="window.TempoMode.setRmodeDetailTaskLabel('${task.id}', 'Now');"
                                            class="w-full text-left px-3 py-1.5 hover:bg-[#FDFBF6] flex items-center justify-between text-[#202124] ${priorityBadge === 'Now' ? 'font-bold text-[#D99E87]' : ''}">
                                        <span>${isViLocale() ? 'Làm ngay' : 'Now'}</span>
                                        ${priorityBadge === 'Now' ? '<span>✓</span>' : ''}
                                    </button>
                                    <button type="button"
                                            onclick="window.TempoMode.setRmodeDetailTaskLabel('${task.id}', 'Then');"
                                            class="w-full text-left px-3 py-1.5 hover:bg-[#FDFBF6] flex items-center justify-between text-[#202124] ${priorityBadge === 'Then' ? 'font-bold text-[#A6753A]' : ''}">
                                        <span>${isViLocale() ? 'Sau đó' : 'Then'}</span>
                                        ${priorityBadge === 'Then' ? '<span>✓</span>' : ''}
                                    </button>
                                    <button type="button"
                                            onclick="window.TempoMode.setRmodeDetailTaskLabel('${task.id}', 'Later');"
                                            class="w-full text-left px-3 py-1.5 hover:bg-[#FDFBF6] flex items-center justify-between text-[#202124] ${priorityBadge === 'Later' ? 'font-bold text-[#7B96A6]' : ''}">
                                        <span>${isViLocale() ? 'Sau nữa' : 'Later'}</span>
                                        ${priorityBadge === 'Later' ? '<span>✓</span>' : ''}
                                    </button>
                                </div>
                            ` : ''}
                        </div>
                    </div>

                    <!-- Due Date Row -->
                    <div class="flex items-center space-x-2 text-xs sm:text-sm text-[#6F6B68]">
                        <span>Deadline: ${escapeHTML(formatRmodeDeadline(task.deadlineDate || task.deadline, task.deadlineTime))}</span>
                        ${isTaskOverdue(task) ? `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300">${(window.t ? window.t('modes.urgent.overdueBadge') : null) || (isViLocale() ? 'TRỄ DEADLINE' : 'OVERDUE')}</span>` : ''}
                        ${(!isTaskOverdue(task) && isTaskMissedSchedule(plannedItem || task)) ? `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-stone-100 text-stone-700 border border-stone-300">${isViLocale() ? 'TASK QUÁ LỊCH' : 'MISSED SCHEDULE'}</span>` : ''}
                        <button type="button"
                                onclick="window.TempoMode.toggleRmodeDetailDeadlineEdit()"
                                class="text-[#D99E87] font-semibold hover:underline cursor-pointer">
                            ${isRmodeDetailEditingDeadline ? (isViLocale() ? 'Hủy' : 'Cancel') : (isViLocale() ? 'Sửa deadline' : 'Edit deadline')}
                        </button>
                    </div>

                    <!-- Inline Deadline Editor -->
                    ${isRmodeDetailEditingDeadline ? `
                        <div class="p-3 bg-white border border-[#E3C7A5] rounded-xl space-y-2 text-xs">
                            <div class="grid grid-cols-2 gap-2">
                                <div>
                                    <label class="block text-[10px] text-gray-500 font-semibold mb-0.5">Date</label>
                                    <input id="rmode-edit-deadline-date" type="date" value="${task.deadlineDate || (task.deadline ? task.deadline.split(' ')[0] : '')}" class="w-full px-2 py-1 text-xs border border-gray-300 rounded-lg">
                                </div>
                                <div>
                                    <label class="block text-[10px] text-gray-500 font-semibold mb-0.5">Time</label>
                                    <input id="rmode-edit-deadline-time" type="time" value="${task.deadlineTime || (task.deadline && task.deadline.includes(':') ? task.deadline.split(' ')[1] : '23:59')}" class="w-full px-2 py-1 text-xs border border-gray-300 rounded-lg">
                                </div>
                            </div>
                            <div class="flex items-center space-x-2">
                                <input id="rmode-edit-no-deadline" type="checkbox" ${task.hasDeadline === false ? 'checked' : ''} class="rounded text-[#D99E87]">
                                <label for="rmode-edit-no-deadline" class="text-xs text-stone-700">${isViLocale() ? 'Chưa có deadline' : 'No fixed deadline'}</label>
                            </div>
                            <div class="flex justify-end pt-1">
                                <button type="button"
                                        onclick="window.TempoMode.saveRmodeDetailDeadlineEdit('${task.id}')"
                                        class="px-3 py-1 bg-[#D99E87] text-white rounded-lg text-xs font-bold hover:bg-[#C98E77] cursor-pointer">
                                    ${isViLocale() ? 'Lưu deadline' : 'Save deadline'}
                                </button>
                            </div>
                        </div>
                    ` : ''}

                    <!-- Subtasks Count Row & Controls -->
                    <div class="flex items-center justify-between text-xs sm:text-sm text-[#6F6B68]">
                        ${totalSubtasks > 0 ? `<span>${completedSubtasks}/${totalSubtasks} ${isViLocale() ? 'bước đã xong' : 'action steps completed'}</span>` : '<span></span>'}
                        <button type="button"
                                onclick="window.TempoMode.toggleRmodeDetailAddSubtask()"
                                class="text-[#D99E87] font-semibold hover:underline cursor-pointer flex items-center space-x-1">
                            <span>${isViLocale() ? '+ Thêm bước nhỏ' : '+ Add action step'}</span>
                        </button>
                    </div>

                    <!-- Add Subtask Input Form -->
                    ${isRmodeDetailAddingSubtask ? `
                        <div class="flex items-center gap-2 p-2.5 bg-white border border-[#E3C7A5] rounded-xl">
                            <input id="rmode-new-subtask-title" 
                                   type="text" 
                                   placeholder="${isViLocale() ? 'Nhập tên bước hành động mới...' : 'Enter new action step...'}"
                                   class="flex-1 px-2.5 py-1 text-xs border border-gray-300 rounded-lg focus:outline-hidden focus:ring-1 focus:ring-[#D99E87]"
                                   onkeydown="if(event.key==='Enter') window.TempoMode.addRmodeDetailSubtask('${task.id}'); if(event.key==='Escape') window.TempoMode.toggleRmodeDetailAddSubtask();" />
                            <button type="button" 
                                    onclick="window.TempoMode.addRmodeDetailSubtask('${task.id}')"
                                    class="px-3 py-1 bg-[#D99E87] text-white rounded-lg text-xs font-bold hover:bg-[#C98E77] cursor-pointer">
                                Add
                            </button>
                            <button type="button" 
                                    onclick="window.TempoMode.toggleRmodeDetailAddSubtask()"
                                    class="px-2 py-1 text-xs text-stone-500 hover:text-stone-800 cursor-pointer">
                                ✕
                            </button>
                        </div>
                    ` : ''}

                    <!-- Subtask List -->
                    <div class="max-h-48 overflow-y-auto space-y-2 pr-1.5 plan-custom-scroll">
                        ${subtasks.length > 0 ? subtasks.map(step => `
                                <div class="flex items-center justify-between space-x-2 text-xs sm:text-sm text-[#4A4540] group bg-white/70 hover:bg-white p-2 rounded-xl border border-[#EDE2D5] transition">
                                    <div class="flex items-center space-x-2.5 min-w-0 flex-1">
                                        <button type="button"
                                                onclick="window.TempoMode.toggleRmodeDetailSubtask('${task.id}', '${step.id}')"
                                            class="w-4 h-4 rounded border border-[#E3C7A5] flex items-center justify-center text-[10px] font-bold transition shrink-0 cursor-pointer ${step.completed ? 'bg-[#92A491] border-[#92A491] text-white' : 'bg-white border-[#E3C7A5] text-transparent hover:border-[#D99E87]'}"
                                            title="${isViLocale() ? 'Đánh dấu bước nhỏ' : 'Toggle step'}">
                                        ✓
                                    </button>
                                    ${editingRmodeSubtaskId === step.id ? `
                                        <div class="flex items-center gap-1.5 flex-1 min-w-0">
                                            <input id="rmode-edit-subtask-input-${step.id}" 
                                                   type="text" 
                                                   value="${escapeHTML(step.title || '')}" 
                                                   class="flex-1 px-2 py-0.5 text-xs border border-[#D99E87] rounded-md bg-white focus:outline-hidden"
                                                   onkeydown="if(event.key==='Enter') window.TempoMode.saveRmodeDetailSubtaskTitle('${task.id}', '${step.id}'); if(event.key==='Escape') window.TempoMode.toggleRmodeDetailSubtaskEdit(null);" />
                                            <button type="button" 
                                                    onclick="window.TempoMode.saveRmodeDetailSubtaskTitle('${task.id}', '${step.id}')" 
                                                    class="text-xs text-[#D99E87] font-bold px-1 hover:underline cursor-pointer">Save</button>
                                            <button type="button" 
                                                    onclick="window.TempoMode.toggleRmodeDetailSubtaskEdit(null)" 
                                                    class="text-xs text-stone-500 px-1 hover:underline cursor-pointer">Cancel</button>
                                        </div>
                                    ` : `
                                        <span class="truncate ${step.completed ? 'line-through text-stone-400' : ''}">${escapeHTML(step.title)}</span>
                                        <button type="button" 
                                                onclick="window.TempoMode.toggleRmodeDetailSubtaskEdit('${step.id}')" 
                                                class="text-stone-400 hover:text-[#D99E87] text-[11px] px-1 opacity-0 group-hover:opacity-100 transition cursor-pointer" 
                                                title="${isViLocale() ? 'Chỉnh sửa bước nhỏ' : 'Edit step'}">✎</button>
                                    `}
                                </div>
                                <button type="button" 
                                        onclick="window.TempoMode.removeRmodeDetailSubtask('${task.id}', '${step.id}')"
                                        class="text-stone-300 hover:text-rose-500 text-xs px-1.5 transition opacity-60 group-hover:opacity-100 cursor-pointer"
                                        title="${isViLocale() ? 'Xóa bước nhỏ' : 'Delete step'}">
                                    ✕
                                </button>
                            </div>
                        `).join('') : `
                            <div class="text-xs text-stone-400 italic py-1">${isViLocale() ? 'Chưa có bước nhỏ nào' : 'No subtasks yet'}</div>
                        `}
                    </div>

                    <!-- Note Row -->
                    ${isRmodeDetailEditingNote ? `
                        <div class="p-3 bg-white border border-[#E3C7A5] rounded-xl space-y-2 text-xs">
                            <label class="block text-[10px] text-gray-500 font-semibold">${isViLocale() ? 'Ghi chú Công việc / Mô tả' : 'Task Note / Description'}</label>
                            <textarea id="rmode-note-editor-text" 
                                      rows="3" 
                                      class="w-full p-2 text-xs border border-gray-300 rounded-lg focus:outline-hidden focus:ring-1 focus:ring-[#D99E87]"
                                      placeholder="${isViLocale() ? 'Thêm chi tiết, liên kết hoặc ghi chú cho task này...' : 'Add details, links, or notes for this task...'}">${escapeHTML(noteText)}</textarea>
                            <div class="flex justify-between items-center pt-1">
                                ${noteText ? `
                                    <button type="button" 
                                            onclick="window.TempoMode.deleteRmodeDetailNote('${task.id}')"
                                            class="text-xs text-rose-600 hover:underline cursor-pointer">
                                        ${isViLocale() ? 'Xóa ghi chú' : 'Delete note'}
                                    </button>
                                ` : '<div></div>'}
                                <div class="flex space-x-2">
                                    <button type="button" 
                                            onclick="window.TempoMode.toggleRmodeDetailNoteEdit()"
                                            class="px-2.5 py-1 text-xs text-stone-600 border border-stone-300 rounded-lg hover:bg-stone-100 cursor-pointer">
                                        Cancel
                                    </button>
                                    <button type="button" 
                                            onclick="window.TempoMode.saveRmodeDetailNote('${task.id}')"
                                            class="px-3 py-1 bg-[#D99E87] text-white rounded-lg text-xs font-bold hover:bg-[#C98E77] cursor-pointer">
                                        ${isViLocale() ? 'Lưu ghi chú' : 'Save note'}
                                    </button>
                                </div>
                            </div>
                        </div>
                    ` : (noteText ? `
                        <div class="text-xs sm:text-sm text-[#4A4540] pt-1 flex items-start justify-between gap-2 bg-[#F6F4EE]/60 border border-[#EAE4DF] rounded-xl p-2.5">
                            <div class="min-w-0 flex-1">
                                <strong class="text-[#D9A18B]">${isViLocale() ? 'Ghi chú:' : 'Note:'}</strong> <span class="whitespace-pre-line text-[#4A4540]">${escapeHTML(noteText)}</span>
                            </div>
                            <button type="button"
                                    onclick="window.TempoMode.toggleRmodeDetailNoteEdit()"
                                    class="text-[#D99E87] hover:text-[#C98E77] text-xs font-semibold shrink-0 cursor-pointer flex items-center space-x-1"
                                    title="${isViLocale() ? 'Chỉnh sửa ghi chú' : 'Edit note'}">
                                <span>${isViLocale() ? 'Chỉnh sửa ghi chú' : 'Edit note'}</span>
                                <span>✎</span>
                            </button>
                        </div>
                    ` : `
                        <div class="pt-1">
                            <button type="button"
                                    onclick="window.TempoMode.toggleRmodeDetailNoteEdit()"
                                    class="text-xs font-bold text-[#D9A18B] hover:underline cursor-pointer flex items-center space-x-1">
                                <span>${isViLocale() ? '+ Thêm ghi chú' : '+ Add note'}</span>
                            </button>
                        </div>
                    `)}

                    <!-- Action Buttons (2x2 grid) -->
                    <div class="grid grid-cols-2 gap-3 pt-3">
                        <!-- 1. Mark as done / active -->
                        <button type="button"
                                onclick="window.TempoMode.toggleRmodeDetailTaskComplete('${task.id}')"
                                class="py-2.5 px-4 rounded-xl font-bold text-xs sm:text-sm text-white bg-[#92A491] hover:bg-[#829381] shadow-2xs transition text-center cursor-pointer">
                            ${isDone ? (isViLocale() ? 'Đang thực hiện' : 'Mark as active') : (isViLocale() ? 'Hoàn thành' : 'Mark as done')}
                        </button>

                        <!-- 2. Focus now -->
                        <button type="button"
                                onclick="window.TempoMode.handleRmodeTaskFocus('${task.id}')"
                                class="py-2.5 px-4 rounded-xl font-bold text-xs sm:text-sm text-white bg-[#D7A690] hover:bg-[#C98E77] shadow-2xs transition flex items-center justify-center space-x-1.5 cursor-pointer">
                            <span>▶ ${isViLocale() ? 'Làm ngay' : 'Focus now'}</span>
                        </button>

                        <!-- 3. Reschedule -->
                        <button type="button"
                                onclick="window.TempoMode.handleRmodeTaskReschedule('${task.id}')"
                                class="py-2.5 px-4 rounded-xl font-bold text-xs sm:text-sm text-[#3A4B3D] bg-white border border-[#8D9B8A] hover:bg-stone-50 transition text-center cursor-pointer">
                            ${isViLocale() ? 'Đổi lịch' : 'Reschedule'}
                        </button>

                        <!-- 4. Clear this task -->
                        <button type="button"
                                onclick="window.TempoMode.promptClearRmodeTask('${task.id}')"
                                class="py-2.5 px-4 rounded-xl font-bold text-xs sm:text-sm text-[#C53B27] bg-white border border-[#D99E87] hover:bg-rose-50/40 transition text-center cursor-pointer">
                            ${isViLocale() ? 'Xóa task này' : 'Clear this task'}
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    // =========================================================================
    // URMODE (EMERGENCY) TASK DETAIL POPUP MODAL (REUSING WORKPLAN UI & ACTIONS)
    // =========================================================================

    let activeUrmodeDetailTaskId = null;
    let isUrmodeDetailEditingTitle = false;
    let isUrmodeDetailEditingDeadline = false;
    let isUrmodeDetailEditingNote = false;
    let isUrmodeDetailLabelMenuOpen = false;
    let isUrmodeDetailAddingSubtask = false;
    let editingUrmodeSubtaskId = null;

    const renderedUrmodeTasksMap = new Map();

    function getUrmodeActivePlan() {
        let plan = null;
        if (window.TempoPlanStore && typeof window.TempoPlanStore.getActivePlan === 'function') {
            plan = window.TempoPlanStore.getActivePlan('emergency');
        }
        if ((!plan || !plan.plannedTasks || plan.plannedTasks.length === 0) && window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.getConfirmedPlan === 'function') {
            const flowPlan = window.TempoEmergencyFlow.getConfirmedPlan();
            if (flowPlan && flowPlan.plannedTasks && flowPlan.plannedTasks.length > 0) plan = flowPlan;
        }
        if ((!plan || !plan.plannedTasks || plan.plannedTasks.length === 0) && window.TempoPlanStore && typeof window.TempoPlanStore.getActivePlan === 'function') {
            const defPlan = window.TempoPlanStore.getActivePlan('default');
            if (defPlan && defPlan.plannedTasks && defPlan.plannedTasks.length > 0) plan = defPlan;
        }
        if ((!plan || !plan.plannedTasks || plan.plannedTasks.length === 0) && window.TempoPlanWorkspace && typeof window.TempoPlanWorkspace.getActivePlan === 'function') {
            const wsPlan = window.TempoPlanWorkspace.getActivePlan();
            if (wsPlan && wsPlan.plannedTasks && wsPlan.plannedTasks.length > 0) plan = wsPlan;
        }
        if (!plan || !plan.plannedTasks || plan.plannedTasks.length === 0) {
            try {
                const key = getWorkingPlanStorageKey();
                const saved = localStorage.getItem(key);
                if (saved) {
                    const parsed = JSON.parse(saved);
                    if (parsed && Array.isArray(parsed.plannedTasks) && parsed.plannedTasks.length > 0) plan = parsed;
                }
            } catch (e) {}
        }
        if (plan) {
            const currentUserId = (window.TempoAuth && typeof window.TempoAuth.getCurrentUserId === 'function') 
                ? window.TempoAuth.getCurrentUserId() : null;
            if (currentUserId) {
                if (plan.userId && plan.userId !== currentUserId) return null;
                if (plan.user_id && plan.user_id !== currentUserId) return null;
                if (!plan.userId && !plan.user_id) return null;
            }
            if (!Array.isArray(plan.plannedTasks)) plan.plannedTasks = [];
            if (!Array.isArray(plan.unarrangedTasks)) plan.unarrangedTasks = [];
            if (!Array.isArray(plan.tasks)) plan.tasks = [];
        }
        return plan;
    }

    function getUrmodeTaskData(taskId) {
        if (!taskId) return null;
        const sTaskId = String(taskId);
        const plan = getUrmodeActivePlan();
        let matchedTask = null;
        let matchedPlanItem = null;
        const renderedItem = renderedUrmodeTasksMap.get(sTaskId);

        // 1. Direct match from currently rendered task cards map
        if (renderedItem) {
            matchedPlanItem = renderedItem;
            if (renderedItem.task) matchedTask = renderedItem.task;
            else matchedTask = renderedItem;
        }

        // 2. Search in plan.plannedTasks
        if (!matchedTask && plan && Array.isArray(plan.plannedTasks)) {
            for (const pt of plan.plannedTasks) {
                const t = pt.task || pt;
                if (t && (String(t.id) === sTaskId || String(pt.id) === sTaskId || String(pt.taskId) === sTaskId)) {
                    matchedTask = t;
                    matchedPlanItem = pt;
                    break;
                }
            }
        }

        // 3. Search in unarrangedTasks
        if (!matchedTask && plan && Array.isArray(plan.unarrangedTasks)) {
            for (const u of plan.unarrangedTasks) {
                const t = u.task || u;
                if (t && (String(t.id) === sTaskId || String(u.id) === sTaskId)) {
                    matchedTask = t;
                    matchedPlanItem = u;
                    break;
                }
            }
        }

        // 4. Search in unallocatedTasks
        if (!matchedTask && plan && Array.isArray(plan.unallocatedTasks)) {
            for (const u of plan.unallocatedTasks) {
                const t = u.task || u;
                if (t && (String(t.id) === sTaskId || String(u.id) === sTaskId)) {
                    matchedTask = t;
                    matchedPlanItem = u;
                    break;
                }
            }
        }

        // 5. Search in plan.tasks
        if (!matchedTask && plan && Array.isArray(plan.tasks)) {
            for (const t of plan.tasks) {
                if (t && String(t.id) === sTaskId) {
                    matchedTask = t;
                    break;
                }
            }
        }

        // 6. Search in completedTasks or doneTasks
        if (!matchedTask && plan) {
            const cList = Array.isArray(plan.completedTasks) ? plan.completedTasks : (Array.isArray(plan.doneTasks) ? plan.doneTasks : []);
            for (const c of cList) {
                const t = c.task || c;
                if (t && (String(t.id) === sTaskId || String(c.id) === sTaskId)) {
                    matchedTask = t;
                    matchedPlanItem = c;
                    break;
                }
            }
        }

        // 7. Fallback for mock tasks
        const mockTasks = {
            'task-marketing-research': {
                id: 'task-marketing-research',
                name: 'Marketing Research',
                title: 'Marketing Research',
                hasDeadline: true,
                deadlineDate: '2026-10-17',
                deadlineTime: '21:00',
                deadline: '2026-10-17 21:00',
                durationLabel: '2h 30m',
                userLabel: 'Now',
                completed: false,
                description: 'Create a sheet to manage references',
                note: 'Create a sheet to manage references',
                subtasks: [
                    { id: 'sub-1', title: 'Subtask 1: Outline', completed: false, durationMinutes: 30 },
                    { id: 'sub-2', title: 'Subtask 2: Literature Review', completed: false, durationMinutes: 45 },
                    { id: 'sub-3', title: 'Subtask 3: Research Gap', completed: false, durationMinutes: 30 },
                    { id: 'sub-4', title: 'Subtask 4: Methodology', completed: false, durationMinutes: 20 },
                    { id: 'sub-5', title: 'Subtask 5: Data Analysis', completed: false, durationMinutes: 15 },
                    { id: 'sub-6', title: 'Subtask 6: Summary Report', completed: false, durationMinutes: 10 }
                ]
            },
            'task-event-proposal': {
                id: 'task-event-proposal',
                name: 'Event Proposal',
                title: 'Event Proposal',
                hasDeadline: true,
                deadlineDate: '2026-10-18',
                deadlineTime: '22:00',
                deadline: '2026-10-18 22:00',
                durationLabel: '2h 30m',
                userLabel: 'Then',
                completed: false,
                description: 'Coordinate with design team for event collateral',
                note: 'Coordinate with design team for event collateral',
                subtasks: [
                    { id: 'ep-sub-1', title: 'Subtask 1: Budget Draft', completed: false, durationMinutes: 45 },
                    { id: 'ep-sub-2', title: 'Subtask 2: Venue Options', completed: false, durationMinutes: 60 },
                    { id: 'ep-sub-3', title: 'Subtask 3: Guest List', completed: false, durationMinutes: 45 }
                ]
            },
            'task-edit-video': {
                id: 'task-edit-video',
                name: 'Edit Video',
                title: 'Edit Video',
                hasDeadline: true,
                deadlineDate: '2026-10-20',
                deadlineTime: '22:00',
                deadline: '2026-10-20 22:00',
                durationLabel: '2h 30m',
                userLabel: 'Later',
                completed: false,
                description: 'Export in 1080p format for social channels',
                note: 'Export in 1080p format for social channels',
                subtasks: []
            }
        };

        if (!matchedTask && mockTasks[sTaskId]) {
            matchedTask = mockTasks[sTaskId];
        }

        if (!matchedTask && window.TempoToolNotes && typeof window.TempoToolNotes.getAvailableTasks === 'function') {
            const avail = window.TempoToolNotes.getAvailableTasks();
            const found = avail.find(t => t && String(t.id) === sTaskId);
            if (found) {
                matchedTask = found;
            }
        }

        if (matchedTask) {
            try {
                const mockTasksState = JSON.parse(localStorage.getItem(getRmodeMockTasksKey()) || '{}');
                if (typeof mockTasksState[sTaskId] === 'boolean') {
                    matchedTask.completed = mockTasksState[sTaskId];
                }
            } catch (e) {}
        }

        return { plan, task: matchedTask, plannedItem: matchedPlanItem || renderedItem };
    }

    function persistUrmodePlanData(plan, task) {
        if (task) {
            if (renderedUrmodeTasksMap.has(String(task.id))) {
                const item = renderedUrmodeTasksMap.get(String(task.id));
                if (item) {
                    item.task = task;
                    item.name = task.name || item.name;
                    item.completed = !!task.completed;
                    if (task.deadlineDate) {
                        item.dueDate = `Deadline: ${formatPlanDateHeader(task.deadlineDate, task.deadlineDate)}`;
                    }
                    if (Array.isArray(task.subtasks)) {
                        const doneCount = task.subtasks.filter(s => s && s.completed).length;
                        item.subtasksText = `${doneCount}/${task.subtasks.length} subtasks`;
                    }
                }
            }
        }

        if (plan) {
            if (task) {
                let found = false;
                if (Array.isArray(plan.plannedTasks)) {
                    for (const pt of plan.plannedTasks) {
                        const t = pt.task || pt;
                        if (t && (String(t.id) === String(task.id) || String(pt.id) === String(task.id))) {
                            found = true;
                            if (pt.task) Object.assign(pt.task, task);
                            else Object.assign(pt, task);
                            break;
                        }
                    }
                }
                if (!found && Array.isArray(plan.unarrangedTasks)) {
                    for (const u of plan.unarrangedTasks) {
                        const t = u.task || u;
                        if (t && (String(t.id) === String(task.id) || String(u.id) === String(task.id))) {
                            found = true;
                            if (u.task) Object.assign(u.task, task);
                            else Object.assign(u, task);
                            break;
                        }
                    }
                }
                if (!found && Array.isArray(plan.tasks)) {
                    for (const t of plan.tasks) {
                        if (t && String(t.id) === String(task.id)) {
                            found = true;
                            Object.assign(t, task);
                            break;
                        }
                    }
                }
                if (!found) {
                    if (!Array.isArray(plan.plannedTasks)) plan.plannedTasks = [];
                    plan.plannedTasks.push({
                        dayDate: task.deadlineDate || getLocalTodayISO(),
                        dayLabel: 'Hôm nay',
                        startTime: '2:00 PM',
                        endTime: '4:00 PM',
                        executionBadge: task.userLabel || 'Now',
                        task: task
                    });
                }
            }

            try {
                localStorage.setItem('tempo_working_plan', JSON.stringify(plan));
            } catch (e) {}

            if (window.TempoPlanStore && typeof window.TempoPlanStore.saveActivePlan === 'function') {
                window.TempoPlanStore.saveActivePlan('emergency', plan);
                window.TempoPlanStore.saveActivePlan('recovery', plan);
            }
            if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.setConfirmedPlan === 'function') {
                window.TempoEmergencyFlow.setConfirmedPlan(plan);
            }
        }

        // Also sync mock tasks in localStorage if applicable
        if (task) {
            try {
                let mockTasks = JSON.parse(localStorage.getItem(getRmodeMockTasksKey()) || '{}');
                mockTasks[task.id] = !!task.completed;
                const mockMap = {
                    'task-marketing-research': 'rmode-mock-1',
                    'task-event-proposal': 'rmode-mock-2',
                    'task-edit-video': 'rmode-mock-3'
                };
                if (mockMap[task.id]) {
                    mockTasks[mockMap[task.id]] = !!task.completed;
                }
                localStorage.setItem(getRmodeMockTasksKey(), JSON.stringify(mockTasks));
            } catch (e) {}
        }

        renderEmodeHome();
        if (typeof renderActiveModeHome === 'function') {
            renderActiveModeHome();
        }
        if (window.TempoPlanWorkspace && typeof window.TempoPlanWorkspace.render === 'function') {
            window.TempoPlanWorkspace.render();
        }
    }

    function openUrmodeTaskDetailModal(taskId) {
        activeUrmodeDetailTaskId = taskId;
        isUrmodeDetailEditingTitle = false;
        isUrmodeDetailEditingDeadline = false;
        isUrmodeDetailEditingNote = false;
        isUrmodeDetailLabelMenuOpen = false;
        isUrmodeDetailAddingSubtask = false;
        editingUrmodeSubtaskId = null;
        renderUrmodeTaskDetailModalDOM();
    }

    function closeUrmodeTaskDetailModal() {
        activeUrmodeDetailTaskId = null;
        isUrmodeDetailEditingTitle = false;
        isUrmodeDetailEditingDeadline = false;
        isUrmodeDetailEditingNote = false;
        isUrmodeDetailLabelMenuOpen = false;
        isUrmodeDetailAddingSubtask = false;
        editingUrmodeSubtaskId = null;
        const globalRoot = document.getElementById('urmode-task-modal-global-root');
        if (globalRoot) {
            globalRoot.innerHTML = '';
        }
        renderUrmodeTaskDetailModalDOM();
    }

    function isUrmodeTaskDetailModalOpen() {
        return Boolean(activeUrmodeDetailTaskId);
    }

    function renderUrmodeTaskDetailModalDOM() {
        let root = document.getElementById('urmode-task-modal-root');
        if (!root || root.closest('.hidden')) {
            let globalRoot = document.getElementById('urmode-task-modal-global-root');
            if (!globalRoot) {
                globalRoot = document.createElement('div');
                globalRoot.id = 'urmode-task-modal-global-root';
                document.body.appendChild(globalRoot);
            }
            globalRoot.innerHTML = renderUrmodeTaskDetailModalHTML();
            return;
        }
        root.innerHTML = renderUrmodeTaskDetailModalHTML();
    }

    function toggleUrmodeDetailTitleEdit() {
        isUrmodeDetailEditingTitle = !isUrmodeDetailEditingTitle;
        renderUrmodeTaskDetailModalDOM();
        if (isUrmodeDetailEditingTitle) {
            setTimeout(() => {
                const input = document.getElementById('urmode-edit-title-input');
                if (input) {
                    input.focus();
                    input.select();
                }
            }, 50);
        }
    }

    function saveUrmodeDetailTitleEdit(taskId) {
        const input = document.getElementById('urmode-edit-title-input');
        const newTitle = input ? input.value.trim() : '';
        if (!newTitle) return;

        const taskInfo = getUrmodeTaskData(taskId);
        if (!taskInfo || !taskInfo.task) return;

        taskInfo.task.name = newTitle;
        taskInfo.task.title = newTitle;
        if (taskInfo.plannedItem && taskInfo.plannedItem.task) {
            taskInfo.plannedItem.task.name = newTitle;
            taskInfo.plannedItem.task.title = newTitle;
        }

        isUrmodeDetailEditingTitle = false;
        persistUrmodePlanData(taskInfo.plan, taskInfo.task);
        renderUrmodeTaskDetailModalDOM();
    }

    function toggleUrmodeDetailDeadlineEdit() {
        isUrmodeDetailEditingDeadline = !isUrmodeDetailEditingDeadline;
        renderUrmodeTaskDetailModalDOM();
    }

    function saveUrmodeDetailDeadlineEdit(taskId) {
        const dateInput = document.getElementById('urmode-edit-deadline-date');
        const timeInput = document.getElementById('urmode-edit-deadline-time');
        const noDeadlineInput = document.getElementById('urmode-edit-no-deadline');

        const noDeadline = noDeadlineInput ? noDeadlineInput.checked : false;
        const date = dateInput ? dateInput.value : '';
        const time = timeInput ? timeInput.value : '';

        const taskInfo = getUrmodeTaskData(taskId);
        if (!taskInfo || !taskInfo.task) return;

        if (noDeadline) {
            taskInfo.task.hasDeadline = false;
            taskInfo.task.deadlineDate = '';
            taskInfo.task.deadlineTime = '';
            taskInfo.task.deadline = 'No fixed deadline';
        } else {
            taskInfo.task.hasDeadline = true;
            taskInfo.task.deadlineDate = date;
            taskInfo.task.deadlineTime = time || taskInfo.task.deadlineTime || '';
            taskInfo.task.deadline = taskInfo.task.deadlineTime ? `${date} ${taskInfo.task.deadlineTime}` : date;
        }

        delete taskInfo.task.isOverdue;
        taskInfo.task.isOverdue = false;

        if (taskInfo.plannedItem && taskInfo.plannedItem.task) {
            taskInfo.plannedItem.task.hasDeadline = taskInfo.task.hasDeadline;
            taskInfo.plannedItem.task.deadlineDate = taskInfo.task.deadlineDate;
            taskInfo.plannedItem.task.deadlineTime = taskInfo.task.deadlineTime;
            taskInfo.plannedItem.task.deadline = taskInfo.task.deadline;
            delete taskInfo.plannedItem.task.isOverdue;
            taskInfo.plannedItem.task.isOverdue = false;
        }

        isUrmodeDetailEditingDeadline = false;
        persistUrmodePlanData(taskInfo.plan, taskInfo.task);
        renderUrmodeTaskDetailModalDOM();
    }

    function toggleUrmodeDetailNoteEdit() {
        isUrmodeDetailEditingNote = !isUrmodeDetailEditingNote;
        renderUrmodeTaskDetailModalDOM();
        if (isUrmodeDetailEditingNote) {
            setTimeout(() => {
                const textarea = document.getElementById('urmode-note-editor-text');
                if (textarea) {
                    textarea.focus();
                    textarea.select();
                }
            }, 50);
        }
    }

    function saveUrmodeDetailNote(taskId) {
        const input = document.getElementById('urmode-note-editor-text');
        const text = input ? input.value.trim() : '';
        const taskInfo = getUrmodeTaskData(taskId);
        if (!taskInfo || !taskInfo.task) return;

        taskInfo.task.note = text;
        taskInfo.task.description = text;
        if (taskInfo.plannedItem && taskInfo.plannedItem.task) {
            taskInfo.plannedItem.task.note = text;
            taskInfo.plannedItem.task.description = text;
        }

        if (window.TempoToolNotes && typeof window.TempoToolNotes.saveTaskNote === 'function') {
            window.TempoToolNotes.saveTaskNote(taskId, taskInfo.task.name || 'Task', text);
        }

        isUrmodeDetailEditingNote = false;
        persistUrmodePlanData(taskInfo.plan, taskInfo.task);
        renderUrmodeTaskDetailModalDOM();
    }

    function deleteUrmodeDetailNote(taskId) {
        const taskInfo = getUrmodeTaskData(taskId);
        if (!taskInfo || !taskInfo.task) return;

        taskInfo.task.note = '';
        taskInfo.task.description = '';
        if (taskInfo.plannedItem && taskInfo.plannedItem.task) {
            taskInfo.plannedItem.task.note = '';
            taskInfo.plannedItem.task.description = '';
        }

        if (window.TempoToolNotes && typeof window.TempoToolNotes.deleteTaskNote === 'function') {
            window.TempoToolNotes.deleteTaskNote(taskId);
        }

        isUrmodeDetailEditingNote = false;
        persistUrmodePlanData(taskInfo.plan, taskInfo.task);
        renderUrmodeTaskDetailModalDOM();
    }

    function toggleUrmodeDetailTaskComplete(taskId) {
        const taskInfo = getUrmodeTaskData(taskId);
        if (!taskInfo || !taskInfo.task) return;

        const currentDone = !!taskInfo.task.completed;
        const newDone = !currentDone;

        taskInfo.task.completed = newDone;
        if (taskInfo.plannedItem && taskInfo.plannedItem.task) {
            taskInfo.plannedItem.task.completed = newDone;
        }

        persistUrmodePlanData(taskInfo.plan, taskInfo.task);
        renderUrmodeTaskDetailModalDOM();
    }

    function toggleUrmodeDetailSubtask(taskId, subtaskId) {
        const taskInfo = getUrmodeTaskData(taskId);
        if (!taskInfo || !taskInfo.task || !Array.isArray(taskInfo.task.subtasks)) return;

        const step = taskInfo.task.subtasks.find(s => s && String(s.id) === String(subtaskId));
        if (step) {
            step.completed = !step.completed;
            persistUrmodePlanData(taskInfo.plan, taskInfo.task);
            renderUrmodeTaskDetailModalDOM();
        }
    }

    function toggleUrmodeDetailAddSubtask() {
        isUrmodeDetailAddingSubtask = !isUrmodeDetailAddingSubtask;
        renderUrmodeTaskDetailModalDOM();
        if (isUrmodeDetailAddingSubtask) {
            setTimeout(() => {
                const input = document.getElementById('urmode-new-subtask-title');
                if (input) input.focus();
            }, 50);
        }
    }

    function addUrmodeDetailSubtask(taskId) {
        const input = document.getElementById('urmode-new-subtask-title');
        const title = input ? input.value.trim() : '';
        if (!title) return;

        const taskInfo = getUrmodeTaskData(taskId);
        if (!taskInfo || !taskInfo.task) return;

        if (!Array.isArray(taskInfo.task.subtasks)) {
            taskInfo.task.subtasks = [];
        }

        const newSubtask = {
            id: `urmode-sub-${Date.now()}-${Math.floor(Math.random() * 1000)}`,
            title: title,
            completed: false,
            durationMinutes: 15
        };

        taskInfo.task.subtasks.push(newSubtask);
        if (taskInfo.plannedItem && taskInfo.plannedItem.task && taskInfo.plannedItem.task !== taskInfo.task) {
            if (!Array.isArray(taskInfo.plannedItem.task.subtasks)) taskInfo.plannedItem.task.subtasks = [];
            taskInfo.plannedItem.task.subtasks.push(newSubtask);
        }

        isUrmodeDetailAddingSubtask = false;
        persistUrmodePlanData(taskInfo.plan, taskInfo.task);
        renderUrmodeTaskDetailModalDOM();
    }

    function removeUrmodeDetailSubtask(taskId, subtaskId) {
        const taskInfo = getUrmodeTaskData(taskId);
        if (!taskInfo || !taskInfo.task || !Array.isArray(taskInfo.task.subtasks)) return;

        taskInfo.task.subtasks = taskInfo.task.subtasks.filter(s => s && String(s.id) !== String(subtaskId));
        if (taskInfo.plannedItem && taskInfo.plannedItem.task && Array.isArray(taskInfo.plannedItem.task.subtasks)) {
            taskInfo.plannedItem.task.subtasks = taskInfo.plannedItem.task.subtasks.filter(s => s && String(s.id) !== String(subtaskId));
        }

        persistUrmodePlanData(taskInfo.plan, taskInfo.task);
        renderUrmodeTaskDetailModalDOM();
    }

    function toggleUrmodeDetailSubtaskEdit(subtaskId) {
        editingUrmodeSubtaskId = subtaskId;
        renderUrmodeTaskDetailModalDOM();
        if (subtaskId) {
            setTimeout(() => {
                const input = document.getElementById(`urmode-edit-subtask-input-${subtaskId}`);
                if (input) {
                    input.focus();
                    input.select();
                }
            }, 50);
        }
    }

    function saveUrmodeDetailSubtaskTitle(taskId, subtaskId) {
        const input = document.getElementById(`urmode-edit-subtask-input-${subtaskId}`);
        const newTitle = input ? input.value.trim() : '';
        if (!newTitle) return;

        const taskInfo = getUrmodeTaskData(taskId);
        if (!taskInfo || !taskInfo.task || !Array.isArray(taskInfo.task.subtasks)) return;

        const step = taskInfo.task.subtasks.find(s => s && String(s.id) === String(subtaskId));
        if (step) {
            step.title = newTitle;
        }

        editingUrmodeSubtaskId = null;
        persistUrmodePlanData(taskInfo.plan, taskInfo.task);
        renderUrmodeTaskDetailModalDOM();
    }

    function toggleUrmodeDetailLabelMenu() {
        isUrmodeDetailLabelMenuOpen = !isUrmodeDetailLabelMenuOpen;
        renderUrmodeTaskDetailModalDOM();
    }

    function setUrmodeDetailTaskLabel(taskId, newLabel) {
        const taskInfo = getUrmodeTaskData(taskId);
        if (!taskInfo || !taskInfo.task) return;

        taskInfo.task.userLabel = newLabel;
        if (taskInfo.plannedItem) {
            taskInfo.plannedItem.tag = newLabel;
            taskInfo.plannedItem.executionBadge = newLabel;
        }

        isUrmodeDetailLabelMenuOpen = false;
        persistUrmodePlanData(taskInfo.plan, taskInfo.task);
        renderUrmodeTaskDetailModalDOM();
    }

    function promptClearUrmodeTask(taskId) {
        if (!confirm('Bạn có chắc chắn muốn xóa task này khỏi kế hoạch không?')) return;
        const taskInfo = getUrmodeTaskData(taskId);
        if (!taskInfo || !taskInfo.plan) {
            closeUrmodeTaskDetailModal();
            return;
        }

        const plan = taskInfo.plan;
        if (Array.isArray(plan.plannedTasks)) {
            plan.plannedTasks = plan.plannedTasks.filter(item => {
                const t = item.task || item;
                return t && String(t.id) !== String(taskId);
            });
        }
        if (Array.isArray(plan.unarrangedTasks)) {
            plan.unarrangedTasks = plan.unarrangedTasks.filter(item => {
                const t = item.task || item;
                return t && String(t.id) !== String(taskId);
            });
        }
        if (Array.isArray(plan.tasks)) {
            plan.tasks = plan.tasks.filter(t => t && String(t.id) !== String(taskId));
        }

        closeUrmodeTaskDetailModal();
        persistUrmodePlanData(plan);
        if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
            window.TempoApp.showToast('Task removed from working plan.');
        }
    }

    function handleUrmodeTaskFocus(taskId) {
        closeUrmodeTaskDetailModal();
        startTaskFocus(taskId);
    }

    function handleUrmodeTaskReschedule(taskId) {
        closeUrmodeTaskDetailModal();
        if (window.TempoPlanWorkspace && typeof window.TempoPlanWorkspace.openRescheduleModal === 'function') {
            window.TempoPlanWorkspace.openRescheduleModal(taskId);
        }
        if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
            window.TempoApp.navigateTo('tool-workplan', taskId);
        } else {
            window.location.hash = '#tool-workplan';
        }
    }

    function renderUrmodeTaskDetailModalHTML() {
        if (!activeUrmodeDetailTaskId) return '';

        const taskInfo = getUrmodeTaskData(activeUrmodeDetailTaskId);
        if (!taskInfo || !taskInfo.task) return '';

        const task = taskInfo.task;
        const plannedItem = taskInfo.plannedItem;
        const isDone = !!task.completed;

        // Schedule string
        let detailScheduleStr = isViLocale() ? `Lịch linh hoạt • ~${task.durationLabel || '1h'}` : `Flexible schedule • ~${task.durationLabel || '1h'}`;
        const itemDayDate = (plannedItem && plannedItem.dayDate) || task.dayDate || task._dayDate;
        const itemSchedLabel = itemDayDate ? formatScheduledDateLabel(itemDayDate, isViLocale()) : '';
        if (plannedItem && plannedItem.timeHeader) {
            detailScheduleStr = plannedItem.timeHeader;
        } else if (plannedItem && plannedItem.startTime && plannedItem.endTime) {
            detailScheduleStr = `${itemSchedLabel || formatScheduledDateLabel(getLocalTodayISO(), isViLocale())}, ${formatTime12H(plannedItem.startTime)} to ${formatTime12H(plannedItem.endTime)}`;
        } else if (itemSchedLabel) {
            detailScheduleStr = `${itemSchedLabel}, ${isViLocale() ? 'Đã lên lịch' : 'Scheduled'}`;
        } else if (task.timeHeader) {
            detailScheduleStr = task.timeHeader;
        } else if (task.deadlineDate) {
            detailScheduleStr = `Deadline: ${formatPlanDateHeader(task.deadlineDate, task.deadlineDate)}`;
        }

        // Priority Badge (dynamically evaluated from task or plannedItem)
        let priorityBadge = 'Up Next';
        if (task.userLabel === 'Now' || (plannedItem && (plannedItem.tag === 'Now' || plannedItem.executionBadge === 'Now' || plannedItem.isNow))) {
            priorityBadge = 'Now';
        } else if (task.userLabel === 'Then' || task.userLabel === 'Up Next' || (plannedItem && (plannedItem.tag === 'Then' || plannedItem.tag === 'Up Next' || plannedItem.executionBadge === 'Then' || plannedItem.executionBadge === 'Up Next'))) {
            priorityBadge = 'Up Next';
        } else if (task.userLabel === 'Later' || (plannedItem && (plannedItem.tag === 'Later' || plannedItem.executionBadge === 'Later' || plannedItem.isUnscheduled))) {
            priorityBadge = 'Later';
        }
        if (isDone) priorityBadge = 'Done';

        // Subtasks calculations
        const subtasks = Array.isArray(task.subtasks) ? task.subtasks : [];
        const totalSubtasks = subtasks.length;
        const completedSubtasks = subtasks.filter(s => s && s.completed).length;

        // Note / Description
        const noteText = (task.note || task.description || (window.TempoToolNotes && window.TempoToolNotes.getTaskNote ? window.TempoToolNotes.getTaskNote(task.id) : '') || '').trim();

        return `
            <div id="urmode-task-detail-modal" 
                 class="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-stone-900/50 backdrop-blur-xs transition-all duration-150"
                 onclick="if(event.target === this) window.TempoMode.closeUrmodeTaskDetailModal();"
                 role="dialog"
                 aria-modal="true"
                 aria-labelledby="urmode-task-modal-title">
                
                <div class="bg-[#FDFBF6] border border-[#E3C7A5] rounded-3xl p-6 sm:p-7 max-w-lg w-full max-h-[90vh] overflow-y-auto space-y-4 shadow-xl relative text-left"
                     onclick="event.stopPropagation();">
                    
                    <!-- Close Button (✕) -->
                    <button type="button" 
                            onclick="window.TempoMode.closeUrmodeTaskDetailModal()"
                            class="absolute top-5 right-5 w-8 h-8 rounded-full bg-[#F3EDE2] hover:bg-[#EAE0D1] text-[#6B5E51] hover:text-[#2D2823] flex items-center justify-center text-sm font-bold transition cursor-pointer"
                            aria-label="${isViLocale() ? 'Đóng chi tiết công việc' : 'Close task detail'}">
                        ✕
                    </button>

                    <!-- Schedule Header -->
                    <div class="text-xs sm:text-sm font-bold text-[#D9A18B] tracking-wide pr-8">
                        ${escapeHTML(detailScheduleStr)}
                    </div>

                    <!-- Title and Priority Badge Row -->
                    <div class="flex items-center justify-between gap-3 pb-1">
                        <div class="flex-1 min-w-0 pr-2">
                            ${isUrmodeDetailEditingTitle ? `
                                <div class="flex items-center gap-2">
                                    <input id="urmode-edit-title-input" 
                                           type="text" 
                                           value="${escapeHTML(task.name || '')}" 
                                           class="w-full px-3 py-1.5 text-base font-bold text-[#202124] border border-[#D99E87] rounded-xl bg-white focus:outline-hidden focus:ring-2 focus:ring-[#D99E87]"
                                           onkeydown="if(event.key==='Enter') window.TempoMode.saveUrmodeDetailTitleEdit('${task.id}'); if(event.key==='Escape') window.TempoMode.toggleUrmodeDetailTitleEdit();" />
                                    <button type="button" 
                                            onclick="window.TempoMode.saveUrmodeDetailTitleEdit('${task.id}')"
                                            class="px-3 py-1.5 bg-[#D99E87] text-white rounded-xl text-xs font-bold hover:bg-[#C98E77] cursor-pointer">
                                        Save
                                    </button>
                                    <button type="button" 
                                            onclick="window.TempoMode.toggleUrmodeDetailTitleEdit()"
                                            class="px-2.5 py-1.5 border border-stone-300 text-stone-600 rounded-xl text-xs font-bold hover:bg-stone-100 cursor-pointer">
                                        Cancel
                                    </button>
                                </div>
                            ` : `
                                <div class="flex items-center gap-2 group">
                                    <h2 id="urmode-task-modal-title" class="font-heading text-xl sm:text-2xl font-bold text-[#202124] truncate ${isDone ? 'line-through text-stone-400' : ''}">
                                        ${escapeHTML(task.name || 'Untitled Task')}
                                    </h2>
                                    <button type="button" 
                                            onclick="window.TempoMode.toggleUrmodeDetailTitleEdit()" 
                                            class="text-[#D99E87] hover:text-[#C98E77] text-xs font-semibold p-1 hover:bg-[#F3EDE2] rounded-md transition cursor-pointer" 
                                            title="${isViLocale() ? 'Chỉnh sửa tên task' : 'Edit task name'}">
                                        ✎
                                    </button>
                                </div>
                            `}
                        </div>

                        <!-- Priority Badge with Dropdown -->
                        <div class="relative inline-block shrink-0">
                            <button type="button"
                                    ${isDone ? 'disabled' : `onclick="window.TempoMode.toggleUrmodeDetailLabelMenu()"`}
                                    class="px-3 py-1 rounded-full text-xs font-bold transition flex items-center space-x-1 ${
                                        isDone
                                            ? 'bg-[#E8EFE8] text-[#556B54]'
                                            : (priorityBadge === 'Now' ? 'bg-[#D79277] text-white hover:bg-[#C98E77]' : (priorityBadge === 'Up Next' || priorityBadge === 'Then' ? 'bg-[#D3DFE4] text-[#5A6B73] hover:bg-[#C5D3D9]' : 'bg-[#EAE4DF] text-[#78716C] hover:bg-[#DDD6D0]'))
                                    } ${isDone ? 'cursor-default' : 'cursor-pointer'}">
                                <span>${isDone ? (isViLocale() ? 'Hoàn thành' : 'Done') : (priorityBadge === 'Now' ? (isViLocale() ? 'Làm ngay' : 'Now') : (priorityBadge === 'Later' ? (isViLocale() ? 'Để sau' : 'Later') : (priorityBadge || 'Up Next')))}</span>
                                ${!isDone ? '<span class="text-[10px] ml-0.5">▾</span>' : ''}
                            </button>

                            ${(!isDone && isUrmodeDetailLabelMenuOpen) ? `
                                <div class="absolute right-0 mt-1.5 w-32 bg-white border border-[#EAE4DF] rounded-xl shadow-lg z-20 py-1 text-xs">
                                    <button type="button"
                                            onclick="window.TempoMode.setUrmodeDetailTaskLabel('${task.id}', 'Now');"
                                            class="w-full text-left px-3 py-1.5 hover:bg-[#FDFBF6] flex items-center justify-between text-[#202124] ${priorityBadge === 'Now' ? 'font-bold text-[#D79277]' : ''}">
                                        <span>${isViLocale() ? 'Làm ngay' : 'Now'}</span>
                                        ${priorityBadge === 'Now' ? '<span>✓</span>' : ''}
                                    </button>
                                    <button type="button"
                                            onclick="window.TempoMode.setUrmodeDetailTaskLabel('${task.id}', 'Up Next');"
                                            class="w-full text-left px-3 py-1.5 hover:bg-[#FDFBF6] flex items-center justify-between text-[#202124] ${(priorityBadge === 'Up Next' || priorityBadge === 'Then') ? 'font-bold text-[#5A6B73]' : ''}">
                                        <span>Up Next</span>
                                        ${(priorityBadge === 'Up Next' || priorityBadge === 'Then') ? '<span>✓</span>' : ''}
                                    </button>
                                    <button type="button"
                                            onclick="window.TempoMode.setUrmodeDetailTaskLabel('${task.id}', 'Later');"
                                            class="w-full text-left px-3 py-1.5 hover:bg-[#FDFBF6] flex items-center justify-between text-[#202124] ${priorityBadge === 'Later' ? 'font-bold text-[#78716C]' : ''}">
                                        <span>${isViLocale() ? 'Sau nữa' : 'Later'}</span>
                                        ${priorityBadge === 'Later' ? '<span>✓</span>' : ''}
                                    </button>
                                </div>
                            ` : ''}
                        </div>
                    </div>

                    <!-- Due Date Row -->
                    <div class="flex items-center space-x-2 text-xs sm:text-sm text-[#6F6B68]">
                        <span>Deadline: ${escapeHTML(formatRmodeDeadline(task.deadlineDate || task.deadline, task.deadlineTime))}</span>
                        ${isTaskOverdue(task) ? `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300">${(window.t ? window.t('modes.urgent.overdueBadge') : null) || (isViLocale() ? 'TRỄ DEADLINE' : 'OVERDUE')}</span>` : ''}
                        ${(!isTaskOverdue(task) && isTaskMissedSchedule(plannedItem || task)) ? `<span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-stone-100 text-stone-700 border border-stone-300">${isViLocale() ? 'TASK QUÁ LỊCH' : 'MISSED SCHEDULE'}</span>` : ''}
                        <button type="button"
                                onclick="window.TempoMode.toggleUrmodeDetailDeadlineEdit()"
                                class="text-[#D99E87] font-semibold hover:underline cursor-pointer">
                            ${isUrmodeDetailEditingDeadline ? (isViLocale() ? 'Hủy' : 'Cancel') : (isViLocale() ? 'Sửa deadline' : 'Edit deadline')}
                        </button>
                    </div>

                    <!-- Inline Deadline Editor -->
                    ${isUrmodeDetailEditingDeadline ? `
                        <div class="p-3 bg-white border border-[#E3C7A5] rounded-xl space-y-2 text-xs">
                            <div class="grid grid-cols-2 gap-2">
                                <div>
                                    <label class="block text-[10px] text-gray-500 font-semibold mb-0.5">Date</label>
                                    <input id="urmode-edit-deadline-date" type="date" value="${task.deadlineDate || (task.deadline ? task.deadline.split(' ')[0] : '')}" class="w-full px-2 py-1 text-xs border border-gray-300 rounded-lg">
                                </div>
                                <div>
                                    <label class="block text-[10px] text-gray-500 font-semibold mb-0.5">Time</label>
                                    <input id="urmode-edit-deadline-time" type="time" value="${task.deadlineTime || (task.deadline && task.deadline.includes(':') ? task.deadline.split(' ')[1] : '23:59')}" class="w-full px-2 py-1 text-xs border border-gray-300 rounded-lg">
                                </div>
                            </div>
                            <div class="flex items-center space-x-2">
                                <input id="urmode-edit-no-deadline" type="checkbox" ${task.hasDeadline === false ? 'checked' : ''} class="rounded text-[#D99E87]">
                                <label for="urmode-edit-no-deadline" class="text-xs text-stone-700">${isViLocale() ? 'Chưa có deadline' : 'No fixed deadline'}</label>
                            </div>
                            <div class="flex justify-end pt-1">
                                <button type="button"
                                        onclick="window.TempoMode.saveUrmodeDetailDeadlineEdit('${task.id}')"
                                        class="px-3 py-1 bg-[#D99E87] text-white rounded-lg text-xs font-bold hover:bg-[#C98E77] cursor-pointer">
                                    ${isViLocale() ? 'Lưu deadline' : 'Save deadline'}
                                </button>
                            </div>
                        </div>
                    ` : ''}

                    <!-- Subtasks Count Row & Controls -->
                    <div class="flex items-center justify-between text-xs sm:text-sm text-[#6F6B68]">
                        ${totalSubtasks > 0 ? `<span>${completedSubtasks}/${totalSubtasks} ${isViLocale() ? 'bước đã xong' : 'action steps completed'}</span>` : '<span></span>'}
                        <button type="button"
                                onclick="window.TempoMode.toggleUrmodeDetailAddSubtask()"
                                class="text-[#D99E87] font-semibold hover:underline cursor-pointer flex items-center space-x-1">
                            <span>${isViLocale() ? '+ Thêm bước nhỏ' : '+ Add action step'}</span>
                        </button>
                    </div>

                    <!-- Add Subtask Input Form -->
                    ${isUrmodeDetailAddingSubtask ? `
                        <div class="flex items-center gap-2 p-2.5 bg-white border border-[#E3C7A5] rounded-xl">
                            <input id="urmode-new-subtask-title" 
                                   type="text" 
                                   placeholder="${isViLocale() ? 'Nhập tên bước hành động mới...' : 'Enter new action step...'}"
                                   class="flex-1 px-2.5 py-1 text-xs border border-gray-300 rounded-lg focus:outline-hidden focus:ring-1 focus:ring-[#D99E87]"
                                   onkeydown="if(event.key==='Enter') window.TempoMode.addUrmodeDetailSubtask('${task.id}'); if(event.key==='Escape') window.TempoMode.toggleUrmodeDetailAddSubtask();" />
                            <button type="button" 
                                    onclick="window.TempoMode.addUrmodeDetailSubtask('${task.id}')"
                                    class="px-3 py-1 bg-[#D99E87] text-white rounded-lg text-xs font-bold hover:bg-[#C98E77] cursor-pointer">
                                Add
                            </button>
                            <button type="button" 
                                    onclick="window.TempoMode.toggleUrmodeDetailAddSubtask()"
                                    class="px-2 py-1 text-xs text-stone-500 hover:text-stone-800 cursor-pointer">
                                ✕
                            </button>
                        </div>
                    ` : ''}

                    <!-- Subtask List -->
                    <div class="max-h-48 overflow-y-auto space-y-2 pr-1.5 plan-custom-scroll">
                        ${subtasks.length > 0 ? subtasks.map(step => `
                            <div class="flex items-center justify-between space-x-2 text-xs sm:text-sm text-[#4A4540] group bg-white/70 hover:bg-white p-2 rounded-xl border border-[#EDE2D5] transition">
                                <div class="flex items-center space-x-2.5 min-w-0 flex-1">
                                    <button type="button"
                                            onclick="window.TempoMode.toggleUrmodeDetailSubtask('${task.id}', '${step.id}')"
                                            class="w-4 h-4 rounded border border-[#E3C7A5] flex items-center justify-center text-[10px] font-bold transition shrink-0 cursor-pointer ${step.completed ? 'bg-[#92A491] border-[#92A491] text-white' : 'bg-white border-[#E3C7A5] text-transparent hover:border-[#D99E87]'}"
                                            title="${isViLocale() ? 'Đánh dấu bước nhỏ' : 'Toggle step'}">
                                        ✓
                                    </button>
                                    ${editingUrmodeSubtaskId === step.id ? `
                                        <div class="flex items-center gap-1.5 flex-1 min-w-0">
                                            <input id="urmode-edit-subtask-input-${step.id}" 
                                                   type="text" 
                                                   value="${escapeHTML(step.title || '')}" 
                                                   class="flex-1 px-2 py-0.5 text-xs border border-[#D99E87] rounded-md bg-white focus:outline-hidden"
                                                   onkeydown="if(event.key==='Enter') window.TempoMode.saveUrmodeDetailSubtaskTitle('${task.id}', '${step.id}'); if(event.key==='Escape') window.TempoMode.toggleUrmodeDetailSubtaskEdit(null);" />
                                            <button type="button" 
                                                    onclick="window.TempoMode.saveUrmodeDetailSubtaskTitle('${task.id}', '${step.id}')" 
                                                    class="text-xs text-[#D99E87] font-bold px-1 hover:underline cursor-pointer">Save</button>
                                            <button type="button" 
                                                    onclick="window.TempoMode.toggleUrmodeDetailSubtaskEdit(null)" 
                                                    class="text-xs text-stone-500 px-1 hover:underline cursor-pointer">Cancel</button>
                                        </div>
                                    ` : `
                                        <span class="truncate ${step.completed ? 'line-through text-stone-400' : ''}">${escapeHTML(step.title)}</span>
                                        <button type="button" 
                                                onclick="window.TempoMode.toggleUrmodeDetailSubtaskEdit('${step.id}')" 
                                                class="opacity-0 group-hover:opacity-100 text-[#D99E87] hover:text-[#C98E77] text-xs font-semibold px-1 transition cursor-pointer" 
                                                title="${isViLocale() ? 'Chỉnh sửa bước nhỏ' : 'Edit step'}">
                                            ✎
                                        </button>
                                    `}
                                </div>
                                <button type="button"
                                        onclick="window.TempoMode.removeUrmodeDetailSubtask('${task.id}', '${step.id}')"
                                        class="opacity-0 group-hover:opacity-100 text-stone-400 hover:text-rose-600 text-xs px-1.5 py-0.5 rounded transition cursor-pointer"
                                        title="${isViLocale() ? 'Xóa bước nhỏ' : 'Delete step'}">
                                    ✕
                                </button>
                            </div>
                        `).join('') : `
                            <div class="p-3 text-xs text-stone-400 italic text-center border border-dashed border-[#EDE2D5] rounded-xl bg-white/40">
                                No subtasks yet
                            </div>
                        `}
                    </div>

                    <!-- Note / Description Section -->
                    ${isUrmodeDetailEditingNote ? `
                        <div class="p-3 bg-white border border-[#E3C7A5] rounded-xl space-y-2">
                            <label class="block text-xs font-bold text-[#D9A18B]">${isViLocale() ? 'Ghi chú Công việc' : 'Task Note'}</label>
                            <textarea id="urmode-note-editor-text" 
                                      rows="3" 
                                      class="w-full p-2 text-xs border border-gray-300 rounded-lg focus:outline-hidden focus:ring-1 focus:ring-[#D99E87]"
                                      placeholder="${isViLocale() ? 'Thêm chi tiết, liên kết hoặc ghi chú cho task này...' : 'Add details, links, or notes for this task...'}">${escapeHTML(noteText)}</textarea>
                            <div class="flex justify-between items-center pt-1">
                                ${noteText ? `
                                    <button type="button" 
                                            onclick="window.TempoMode.deleteUrmodeDetailNote('${task.id}')"
                                            class="text-xs text-rose-600 hover:underline cursor-pointer">
                                        ${isViLocale() ? 'Xóa ghi chú' : 'Delete note'}
                                    </button>
                                ` : '<div></div>'}
                                <div class="flex space-x-2">
                                    <button type="button" 
                                            onclick="window.TempoMode.toggleUrmodeDetailNoteEdit()"
                                            class="px-2.5 py-1 text-xs text-stone-600 border border-stone-300 rounded-lg hover:bg-stone-100 cursor-pointer">
                                        Cancel
                                    </button>
                                    <button type="button" 
                                            onclick="window.TempoMode.saveUrmodeDetailNote('${task.id}')"
                                            class="px-3 py-1 bg-[#D99E87] text-white rounded-lg text-xs font-bold hover:bg-[#C98E77] cursor-pointer">
                                        ${isViLocale() ? 'Lưu ghi chú' : 'Save note'}
                                    </button>
                                </div>
                            </div>
                        </div>
                    ` : (noteText ? `
                        <div class="text-xs sm:text-sm text-[#4A4540] pt-1 flex items-start justify-between gap-2 bg-[#F6F4EE]/60 border border-[#EAE4DF] rounded-xl p-2.5">
                            <div class="min-w-0 flex-1">
                                <strong class="text-[#D9A18B]">${isViLocale() ? 'Ghi chú:' : 'Note:'}</strong> <span class="whitespace-pre-line text-[#4A4540]">${escapeHTML(noteText)}</span>
                            </div>
                            <button type="button"
                                    onclick="window.TempoMode.toggleUrmodeDetailNoteEdit()"
                                    class="text-[#D99E87] hover:text-[#C98E77] text-xs font-semibold shrink-0 cursor-pointer flex items-center space-x-1"
                                    title="${isViLocale() ? 'Chỉnh sửa ghi chú' : 'Edit note'}">
                                <span>${isViLocale() ? 'Chỉnh sửa ghi chú' : 'Edit note'}</span>
                                <span>✎</span>
                            </button>
                        </div>
                    ` : `
                        <div class="pt-1">
                            <button type="button"
                                    onclick="window.TempoMode.toggleUrmodeDetailNoteEdit()"
                                    class="text-xs font-bold text-[#D9A18B] hover:underline cursor-pointer flex items-center space-x-1">
                                <span>${isViLocale() ? '+ Tạo ghi chú' : '+ Add note'}</span>
                            </button>
                        </div>
                    `)}

                    <!-- Action Buttons (2x2 grid) -->
                    <div class="grid grid-cols-2 gap-3 pt-3">
                        <!-- 1. Mark as done / active -->
                        <button type="button"
                                onclick="window.TempoMode.toggleUrmodeDetailTaskComplete('${task.id}')"
                                class="py-2.5 px-4 rounded-xl font-bold text-xs sm:text-sm text-white bg-[#92A491] hover:bg-[#829381] shadow-2xs transition text-center cursor-pointer">
                            ${isDone ? (isViLocale() ? 'Đang thực hiện' : 'Mark as active') : (isViLocale() ? 'Hoàn thành' : 'Mark as done')}
                        </button>

                        <!-- 2. Focus now -->
                        <button type="button"
                                onclick="window.TempoMode.handleUrmodeTaskFocus('${task.id}')"
                                class="py-2.5 px-4 rounded-xl font-bold text-xs sm:text-sm text-white bg-[#D7A690] hover:bg-[#C98E77] shadow-2xs transition flex items-center justify-center space-x-1.5 cursor-pointer">
                            <span>▶ ${isViLocale() ? 'Làm ngay' : 'Focus now'}</span>
                        </button>

                        <!-- 3. Reschedule -->
                        <button type="button"
                                onclick="window.TempoMode.handleUrmodeTaskReschedule('${task.id}')"
                                class="py-2.5 px-4 rounded-xl font-bold text-xs sm:text-sm text-[#3A4B3D] bg-white border border-[#8D9B8A] hover:bg-stone-50 transition text-center cursor-pointer">
                            ${isViLocale() ? 'Đổi lịch' : 'Reschedule'}
                        </button>

                        <!-- 4. Clear this task -->
                        <button type="button"
                                onclick="window.TempoMode.promptClearUrmodeTask('${task.id}')"
                                class="py-2.5 px-4 rounded-xl font-bold text-xs sm:text-sm text-[#C53B27] bg-white border border-[#D99E87] hover:bg-rose-50/40 transition text-center cursor-pointer">
                            ${isViLocale() ? 'Xóa task này' : 'Clear this task'}
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    function renderRecoveryCommunityCard() {
        let allPosts = (window.TempoCommunity && typeof window.TempoCommunity.getAllPosts === 'function')
            ? window.TempoCommunity.getAllPosts()
            : [];
        if (!Array.isArray(allPosts) || allPosts.length === 0) {
            if (window.TempoCommunity && typeof window.TempoCommunity.getInitialPosts === 'function') {
                allPosts = window.TempoCommunity.getInitialPosts();
            }
        }
        const distinctPosts = (window.TempoCommunity && typeof window.TempoCommunity.getDistinctPosts === 'function')
            ? window.TempoCommunity.getDistinctPosts(allPosts, 2)
            : (Array.isArray(allPosts) ? allPosts.slice(0, 2) : []);

        let postsCardsHTML = '';
        if (distinctPosts.length > 0) {
            if (window.TempoCommunity && typeof window.TempoCommunity.renderPreviewPostCardHTML === 'function') {
                postsCardsHTML = distinctPosts.map(p => window.TempoCommunity.renderPreviewPostCardHTML(p)).join('');
            } else if (typeof renderCommunityPreviewsHTML === 'function') {
                postsCardsHTML = renderCommunityPreviewsHTML(distinctPosts);
            }
        } else {
            postsCardsHTML = `
                <div class="h-48 flex flex-col items-center justify-center text-center p-6 space-y-2 text-[#8E8A85]">
                    <img src="assets/comment_action_symbol.png" alt="No posts" class="w-6 h-6 opacity-40 object-contain mb-0.5">
                    <p class="text-xs font-bold text-[#5A5550]">No community posts yet</p>
                    <p class="text-[10.5px] text-[#8E8A85] leading-relaxed">Be the first to share with your peers in the community.</p>
                </div>
            `;
        }

        return `
            <div class="recovery-section-posts bg-[#FEFAF4] border border-[#EAE4DF] rounded-3xl sm:rounded-[32px] p-4.5 sm:p-5 shadow-xs flex flex-col justify-between space-y-3.5 box-border w-full" 
                 data-tempo-ui="recovery-community">
                <!-- Header -->
                <div class="flex items-center justify-between pb-0.5 w-full">
                    <div class="flex items-center space-x-2.5">
                        <div class="w-8 h-8 rounded-full bg-[#F6E6DE] flex items-center justify-center shrink-0">
                            <img src="assets/comment_action_symbol.png" alt="Community" class="w-4 h-4 object-contain" />
                        </div>
                        <h3 class="font-bold text-base sm:text-lg text-[#55504C] tracking-tight">
                            ${window.t ? window.t('modes.recovery.fromCommunity', {}, (isViLocale() ? 'Cộng đồng Tempo' : 'From the Tempo Community')) : (isViLocale() ? 'Cộng đồng Tempo' : 'From the Tempo Community')}
                        </h3>
                    </div>
                    <button type="button" 
                            id="btn-see-all-posts-recovery"
                            onclick="if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') { window.TempoApp.navigateTo('community'); } else { window.location.hash = '#community?tab=posts'; } if (window.TempoCommunity && typeof window.TempoCommunity.selectTab === 'function') { window.TempoCommunity.selectTab('posts'); }" 
                            class="px-3.5 py-1 rounded-full bg-[#FCEFE8] hover:bg-[#F8E1D5] text-[#DE8662] text-xs font-bold transition flex items-center space-x-1 cursor-pointer"
                            aria-label="${isViLocale() ? 'Xem tất cả →' : 'View all →'}" title="${isViLocale() ? 'Xem tất cả →' : 'View all →'}">
                        <span>${(window.t ? (window.t('modes.recovery.viewAll') || window.t('modes.recovery.seeAll')) : null) || (isViLocale() ? 'Xem tất cả' : 'View all')}</span>
                        <span class="text-xs">&rarr;</span>
                    </button>
                </div>

                <!-- Social Post Previews -->
                <div id="recovery-community-posts-list" class="space-y-3 flex-1 flex flex-col justify-between w-full">
                    ${postsCardsHTML}
                </div>
            </div>
        `;
    }

    // Preserved for backwards compatibility - Enjoy Tempo Tools section removed from Rmode
    function renderRecoveryEnjoyToolsSection() {
        return '';
    }


    // Preserved for backwards compatibility
    function renderWeeklyReviewShell(isReady, reviewData) {
        return '';
    }

    function renderRecoveryTodaySection(confirmedPlan, todayStr) {
        return '';
    }

    function renderRecoverySharedEcosystem() {
        return '';
    }

    function renderRecoveryPostsSection() {
        return '';
    }

    // =========================================================================
    // TASK & PLAN INTERACTIONS
    // =========================================================================

    function toggleTaskCompletion(taskId) {
        setTaskCompletionStatus(taskId, undefined);
    }

    function startTaskFocus(taskId) {
        if (window.TempoEmergencyFlow && window.TempoEmergencyFlow.setTaskInProgress) {
            window.TempoEmergencyFlow.setTaskInProgress(taskId, true);
        }
        if (window.TempoPlanStore && window.TempoPlanStore.updateTaskState) {
            window.TempoPlanStore.updateTaskState(taskId, { isInProgress: true });
        }

        if (window.TempoFocusZone && window.TempoFocusZone.open) {
            window.TempoFocusZone.open({ taskId: taskId });
        } else if (window.TempoTriage) {
            window.TempoTriage.launchFocusMode();
            const confirmedPlan = (window.TempoPlanStore && window.TempoPlanStore.getActivePlan)
                ? (window.TempoPlanStore.getActivePlan('emergency') || (window.TempoEmergencyFlow && window.TempoEmergencyFlow.getConfirmedPlan ? window.TempoEmergencyFlow.getConfirmedPlan() : null))
                : (window.TempoEmergencyFlow && window.TempoEmergencyFlow.getConfirmedPlan ? window.TempoEmergencyFlow.getConfirmedPlan() : null);
            const taskItem = confirmedPlan?.plannedTasks?.find(pt => pt.task && pt.task.id === taskId)
                || confirmedPlan?.unarrangedTasks?.find(u => (u && u.task ? u.task.id : u.id) === taskId)
                || confirmedPlan?.unallocatedTasks?.find(u => (u && u.task ? u.task.id : u.id) === taskId)
                || confirmedPlan?.tasks?.find(t => t && t.id === taskId);
            const actualTask = taskItem?.task || taskItem;
            if (actualTask && actualTask.name) {
                const taskNameEl = document.getElementById('focus-task-name');
                if (taskNameEl) {
                    taskNameEl.textContent = actualTask.name;
                }
            }
        }
        renderActiveModeHome();
    }

    function stopForToday() {
        sessionFlags.dismissedTimeEndedToday = true;
        if (window.TempoApp) {
            window.TempoApp.showToast("Stopped for today. Rest and recovery are essential for tomorrow's focus.");
        }
        renderActiveModeHome();
    }

    function keepWorkingToday() {
        sessionFlags.dismissedTimeEndedToday = true;
        if (window.TempoApp) {
            window.TempoApp.showToast("Continuing work today.");
        }
        renderActiveModeHome();
    }

    function dismissStaleWarning() {
        sessionFlags.dismissedStaleWarning = true;
        renderActiveModeHome();
    }

    let isTaskActionSubmitting = false;

    /**
     * Canonical unified task completion operation.
     * Used by:
     * 1. Overdue task card 'Mark as done' button
     * 2. 'Your Task for Now' checkbox
     * 3. 'Tomorrow's Task' checkbox
     * 4. 'Kế hoạch Làm việc của bạn' task item completion toggle
     */
    async function setTaskCompletionStatus(taskId, isCompleted, options = {}) {
        if (!taskId) return false;
        if (isTaskActionSubmitting) return false;
        isTaskActionSubmitting = true;

        let previousCompleted = null;
        let previousInProgress = null;
        let matchedTask = null;
        const sTaskId = String(taskId);

        if (sTaskId.startsWith('rmode-mock-')) {
            let mockTasks = {};
            try {
                mockTasks = JSON.parse(localStorage.getItem(getRmodeMockTasksKey()) || '{}');
            } catch (e) {}
            const curVal = !!mockTasks[sTaskId];
            const targetVal = (typeof isCompleted === 'boolean') ? isCompleted : !curVal;
            mockTasks[sTaskId] = targetVal;
            localStorage.setItem(getRmodeMockTasksKey(), JSON.stringify(mockTasks));

            // Sync with real task if exists
            const mockMap = {
                'rmode-mock-1': 'task-marketing-research',
                'rmode-mock-2': 'task-event-proposal',
                'rmode-mock-3': 'task-edit-video'
            };
            const realId = mockMap[sTaskId];
            if (realId) {
                try {
                    const wpRaw = localStorage.getItem(getWorkingPlanStorageKey()) || localStorage.getItem('tempo_working_plan');
                    if (wpRaw) {
                        const wp = JSON.parse(wpRaw);
                        let mutated = false;
                        if (Array.isArray(wp.plannedTasks)) {
                            const pt = wp.plannedTasks.find(item => item.task && String(item.task.id) === realId);
                            if (pt && pt.task) {
                                pt.task.completed = targetVal;
                                mutated = true;
                            }
                        }
                        if (mutated) {
                            localStorage.setItem(getWorkingPlanStorageKey(), JSON.stringify(wp));
                            localStorage.setItem('tempo_working_plan', JSON.stringify(wp));
                            if (window.TempoPlanStore && typeof window.TempoPlanStore.saveActivePlan === 'function') {
                                window.TempoPlanStore.saveActivePlan('emergency', wp);
                                window.TempoPlanStore.saveActivePlan('recovery', wp);
                            }
                        }
                    }
                } catch(e) {}
            }

            renderRmodeHome();
            if (window.TempoPlanWorkspace && typeof window.TempoPlanWorkspace.render === 'function') {
                window.TempoPlanWorkspace.render();
            }
            isTaskActionSubmitting = false;
            return true;
        }

        try {
            // 1. Retrieve active plan with robust fallback
            const isRecovery = (activeContext === MODES.RECOVERY);
            const activeStorePlan = window.TempoPlanStore && typeof window.TempoPlanStore.getActivePlan === 'function'
                ? (isRecovery ? (window.TempoPlanStore.getActivePlan('recovery') || window.TempoPlanStore.getActivePlan('emergency')) : window.TempoPlanStore.getActivePlan('emergency'))
                : null;
            const flowPlan = window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.getConfirmedPlan === 'function'
                ? window.TempoEmergencyFlow.getConfirmedPlan()
                : null;
            const wsPlan = (window.TempoPlanWorkspace && typeof window.TempoPlanWorkspace.getActivePlan === 'function')
                ? window.TempoPlanWorkspace.getActivePlan()
                : null;
            let localPlan = null;
            try {
                const raw = localStorage.getItem(getWorkingPlanStorageKey()) || localStorage.getItem('tempo_working_plan');
                if (raw) localPlan = JSON.parse(raw);
            } catch (e) {}

            const plan = (activeStorePlan && ((Array.isArray(activeStorePlan.plannedTasks) && activeStorePlan.plannedTasks.length > 0) || (Array.isArray(activeStorePlan.tasks) && activeStorePlan.tasks.length > 0)))
                ? activeStorePlan
                : (flowPlan || wsPlan || localPlan || activeStorePlan);

            if (!plan) {
                throw new Error("Active Working Plan not found.");
            }

            // 2. Identify target task by stable ID across all plan task collections
            if (Array.isArray(plan.plannedTasks)) {
                const pt = plan.plannedTasks.find(item => {
                    const t = (item && item.task) ? item.task : item;
                    return t && String(t.id) === sTaskId;
                });
                if (pt) matchedTask = pt.task || pt;
            }
            if (!matchedTask && Array.isArray(plan.unarrangedTasks)) {
                const u = plan.unarrangedTasks.find(item => {
                    const t = (item && item.task) ? item.task : item;
                    return t && String(t.id) === sTaskId;
                });
                if (u) matchedTask = u.task || u;
            }
            if (!matchedTask && Array.isArray(plan.unallocatedTasks)) {
                const u = plan.unallocatedTasks.find(item => {
                    const t = (item && item.task) ? item.task : item;
                    return t && String(t.id) === sTaskId;
                });
                if (u) matchedTask = u.task || u;
            }
            if (!matchedTask && Array.isArray(plan.tasks)) {
                matchedTask = plan.tasks.find(t => t && String(t.id) === sTaskId);
            }
            if (!matchedTask && Array.isArray(plan.completedTasks)) {
                const c = plan.completedTasks.find(item => {
                    const t = (item && item.task) ? item.task : item;
                    return t && String(t.id) === sTaskId;
                });
                if (c) matchedTask = c.task || c;
            }

            // Also check wsPlan if distinct instance
            if (!matchedTask && wsPlan && wsPlan !== plan) {
                if (Array.isArray(wsPlan.plannedTasks)) {
                    const pt = wsPlan.plannedTasks.find(item => {
                        const t = (item && item.task) ? item.task : item;
                        return t && String(t.id) === sTaskId;
                    });
                    if (pt) matchedTask = pt.task || pt;
                }
                if (!matchedTask && Array.isArray(wsPlan.unarrangedTasks)) {
                    const u = wsPlan.unarrangedTasks.find(item => {
                        const t = (item && item.task) ? item.task : item;
                        return t && String(t.id) === sTaskId;
                    });
                    if (u) matchedTask = u.task || u;
                }
            }

            // Also check flowPlan if distinct instance
            if (!matchedTask && flowPlan && flowPlan !== plan) {
                if (Array.isArray(flowPlan.plannedTasks)) {
                    const pt = flowPlan.plannedTasks.find(item => {
                        const t = (item && item.task) ? item.task : item;
                        return t && String(t.id) === sTaskId;
                    });
                    if (pt) matchedTask = pt.task || pt;
                }
                if (!matchedTask && Array.isArray(flowPlan.unarrangedTasks)) {
                    const u = flowPlan.unarrangedTasks.find(item => {
                        const t = (item && item.task) ? item.task : item;
                        return t && String(t.id) === sTaskId;
                    });
                    if (u) matchedTask = u.task || u;
                }
                if (!matchedTask && Array.isArray(flowPlan.tasks)) {
                    matchedTask = flowPlan.tasks.find(t => t && String(t.id) === sTaskId);
                }
            }

            if (!matchedTask) {
                if (sTaskId.startsWith('rmode-mock-') || activeContext === MODES.RECOVERY) {
                    let mockTasks = {};
                    try {
                        mockTasks = JSON.parse(localStorage.getItem(getRmodeMockTasksKey()) || '{}');
                    } catch (e) {}
                    const curVal = !!mockTasks[sTaskId];
                    mockTasks[sTaskId] = (typeof isCompleted === 'boolean') ? isCompleted : !curVal;
                    localStorage.setItem(getRmodeMockTasksKey(), JSON.stringify(mockTasks));
                    if (activeContext === MODES.RECOVERY) {
                        renderRmodeHome();
                    }
                    isTaskActionSubmitting = false;
                    return true;
                }
                throw new Error("Task not found in active Working Plan.");
            }

            // Snapshot previous state for atomic rollback on persistence failure
            previousCompleted = isTaskExplicitlyCompleted(matchedTask);
            previousInProgress = matchedTask.isInProgress ?? matchedTask.in_progress ?? false;

            const targetCompleted = (typeof isCompleted === 'boolean') ? isCompleted : !previousCompleted;
            const targetInProgress = targetCompleted ? false : (matchedTask.isInProgress || matchedTask.in_progress || false);

            const isOverdue = !!(options.isOverdue || (window.TempoUrmodeFlow && window.TempoUrmodeFlow.isTaskOverdue && window.TempoUrmodeFlow.isTaskOverdue(matchedTask, plan)));

            // 3. Mutate task in active plan
            matchedTask.completed = targetCompleted;
            matchedTask.executionStatus = targetCompleted ? 'completed' : 'pending';
            matchedTask.isInProgress = targetInProgress;
            matchedTask.in_progress = targetInProgress;
            if (targetCompleted) {
                matchedTask.completedAt = Date.now();
            } else {
                delete matchedTask.completedAt;
            }

            if (flowPlan && flowPlan !== plan) {
                if (Array.isArray(flowPlan.plannedTasks)) {
                    const fpt = flowPlan.plannedTasks.find(item => item.task && String(item.task.id) === sTaskId);
                    if (fpt && fpt.task) {
                        fpt.task.completed = targetCompleted;
                        fpt.task.isInProgress = targetInProgress;
                        fpt.task.in_progress = targetInProgress;
                    }
                }
            }

            // 4. Update TempoEmergencyFlow explicitly
            if (window.TempoEmergencyFlow) {
                if (typeof window.TempoEmergencyFlow.setTaskCompleted === 'function') {
                    window.TempoEmergencyFlow.setTaskCompleted(taskId, targetCompleted);
                } else if (typeof window.TempoEmergencyFlow.toggleTaskCompleted === 'function') {
                    const curInFlow = (window.TempoEmergencyFlow.isTaskCompleted && window.TempoEmergencyFlow.isTaskCompleted(taskId));
                    if (curInFlow !== targetCompleted) {
                        window.TempoEmergencyFlow.toggleTaskCompleted(taskId);
                    }
                }
                if (typeof window.TempoEmergencyFlow.setConfirmedPlan === 'function') {
                    window.TempoEmergencyFlow.setConfirmedPlan(plan);
                }
            }

            // 5. Persist to TempoPlanStore
            if (window.TempoPlanStore) {
                if (typeof window.TempoPlanStore.updateTaskState === 'function') {
                    await window.TempoPlanStore.updateTaskState(taskId, {
                        completed: targetCompleted,
                        isInProgress: targetInProgress
                    });
                }
                if (typeof window.TempoPlanStore.saveActivePlan === 'function' && plan) {
                    await window.TempoPlanStore.saveActivePlan('emergency', plan);
                    await window.TempoPlanStore.saveActivePlan('recovery', plan);
                }
            }

            // Also persist in localStorage tempo_working_plan and tempo_rmode_mock_tasks
            try {
                localStorage.setItem(getWorkingPlanStorageKey(), JSON.stringify(plan));
                localStorage.setItem('tempo_working_plan', JSON.stringify(plan));
                let mockTasks = {};
                try {
                    mockTasks = JSON.parse(localStorage.getItem(getRmodeMockTasksKey()) || '{}');
                } catch(e) {}
                if (sTaskId === 'task-marketing-research') mockTasks['rmode-mock-1'] = targetCompleted;
                if (sTaskId === 'task-event-proposal') mockTasks['rmode-mock-2'] = targetCompleted;
                if (sTaskId === 'task-edit-video') mockTasks['rmode-mock-3'] = targetCompleted;
                mockTasks[sTaskId] = targetCompleted;
                localStorage.setItem(getRmodeMockTasksKey(), JSON.stringify(mockTasks));
            } catch(e) {}

            // 6. Verify persistence succeeded
            const verifiedPlan = window.TempoPlanStore && typeof window.TempoPlanStore.getActivePlan === 'function'
                ? (window.TempoPlanStore.getActivePlan('emergency') || window.TempoPlanStore.getActivePlan('recovery') || plan)
                : (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.getConfirmedPlan === 'function' ? window.TempoEmergencyFlow.getConfirmedPlan() : plan);

            let verifiedTask = null;
            if (verifiedPlan && Array.isArray(verifiedPlan.plannedTasks)) {
                const vpt = verifiedPlan.plannedTasks.find(item => item.task && String(item.task.id) === sTaskId);
                if (vpt && vpt.task) verifiedTask = vpt.task;
            }
            if (!verifiedTask && verifiedPlan && Array.isArray(verifiedPlan.unarrangedTasks)) {
                const vu = verifiedPlan.unarrangedTasks.find(item => String(item && item.task ? item.task.id : item.id) === sTaskId);
                if (vu) verifiedTask = vu.task || vu;
            }
            if (!verifiedTask && verifiedPlan && Array.isArray(verifiedPlan.tasks)) {
                verifiedTask = verifiedPlan.tasks.find(t => t && String(t.id) === sTaskId);
            }

            if (!verifiedTask || verifiedTask.completed !== targetCompleted) {
                throw new Error("Persistence verification failed: task completed state does not match persisted result.");
            }

            // 7. Success notification ONLY after completion is confirmed
            if (targetCompleted && window.TempoApp) {
                if (typeof window.TempoApp.triggerConfetti === 'function') window.TempoApp.triggerConfetti();
                if (typeof window.TempoApp.showToast === 'function') {
                    if (isOverdue) {
                        window.TempoApp.showToast("Overdue task marked as completed.");
                    } else {
                        window.TempoApp.showToast("Task marked as Done. Taking small steps protects your momentum.");
                    }
                }
            }

            // 8. Recompute and refresh active mode home (Urmode / Rmode dashboard)
            renderActiveModeHome();
            if (window.TempoPlanWorkspace && typeof window.TempoPlanWorkspace.render === 'function') {
                window.TempoPlanWorkspace.render();
            }
            return true;
        } catch (err) {
            console.error("[TempoMode] Task completion operation failed:", err);

            // Roll back in-memory mutation on persistence failure so UI accurately reflects storage
            if (matchedTask && previousCompleted !== null) {
                matchedTask.completed = previousCompleted;
                matchedTask.isInProgress = previousInProgress;
                matchedTask.in_progress = previousInProgress;
                if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.setTaskCompleted === 'function') {
                    window.TempoEmergencyFlow.setTaskCompleted(taskId, previousCompleted);
                }
            }

            if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                window.TempoApp.showToast("Could not update task. Please try again.", 4000);
            }
            renderActiveModeHome();
            return false;
        } finally {
            isTaskActionSubmitting = false;
        }
    }

    async function handleCardTaskComplete(taskId, isChecked = true) {
        return setTaskCompletionStatus(taskId, isChecked);
    }

    async function setSubtaskCompleted(taskId, subtaskId, isCompleted) {
        if (!taskId) return false;
        const targetCompleted = Boolean(isCompleted);
        const sTaskId = String(taskId);
        const sSubtaskId = String(subtaskId || 'default');

        try {
            // 1. Retrieve active plan with robust fallback
            const activeStorePlan = window.TempoPlanStore && typeof window.TempoPlanStore.getActivePlan === 'function'
                ? window.TempoPlanStore.getActivePlan('emergency')
                : null;
            const flowPlan = window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.getConfirmedPlan === 'function'
                ? window.TempoEmergencyFlow.getConfirmedPlan()
                : null;

            const plan = (activeStorePlan && ((Array.isArray(activeStorePlan.plannedTasks) && activeStorePlan.plannedTasks.length > 0) || (Array.isArray(activeStorePlan.tasks) && activeStorePlan.tasks.length > 0)))
                ? activeStorePlan
                : (flowPlan || activeStorePlan);

            if (!plan) {
                console.warn("[TempoMode] Active plan not found for subtask update.");
                return false;
            }

            // 2. Locate target task across all plan collections
            let matchedTask = null;
            if (Array.isArray(plan.plannedTasks)) {
                const pt = plan.plannedTasks.find(item => item.task && String(item.task.id) === sTaskId);
                if (pt && pt.task) matchedTask = pt.task;
            }
            if (!matchedTask && Array.isArray(plan.unarrangedTasks)) {
                const u = plan.unarrangedTasks.find(item => String(item && item.task ? item.task.id : item.id) === sTaskId);
                if (u) matchedTask = u.task || u;
            }
            if (!matchedTask && Array.isArray(plan.unallocatedTasks)) {
                const u = plan.unallocatedTasks.find(item => String(item && item.task ? item.task.id : item.id) === sTaskId);
                if (u) matchedTask = u.task || u;
            }
            if (!matchedTask && Array.isArray(plan.tasks)) {
                matchedTask = plan.tasks.find(t => t && String(t.id) === sTaskId);
            }

            if (!matchedTask) {
                console.warn("[TempoMode] Task not found in active plan:", taskId);
                return false;
            }

            // 3. Mutate subtask state while keeping parent task completion strictly independent
            if (sSubtaskId === 'default' || !Array.isArray(matchedTask.subtasks) || matchedTask.subtasks.length === 0) {
                return false;
            }
            const foundSub = matchedTask.subtasks.find(s => String(s.id) === sSubtaskId);
            if (!foundSub) {
                return false;
            }
            foundSub.completed = targetCompleted;

            // Also mirror in flowPlan if distinct
            if (flowPlan && flowPlan !== plan) {
                let fTask = null;
                if (Array.isArray(flowPlan.plannedTasks)) {
                    const fpt = flowPlan.plannedTasks.find(item => item.task && String(item.task.id) === sTaskId);
                    if (fpt && fpt.task) fTask = fpt.task;
                }
                if (!fTask && Array.isArray(flowPlan.tasks)) {
                    fTask = flowPlan.tasks.find(t => t && String(t.id) === sTaskId);
                }
                if (fTask) {
                    fTask.subtasks = JSON.parse(JSON.stringify(matchedTask.subtasks));
                }
            }

            // 4. Update TempoEmergencyFlow
            if (window.TempoEmergencyFlow) {
                if (typeof window.TempoEmergencyFlow.setSubtaskCompleted === 'function') {
                    window.TempoEmergencyFlow.setSubtaskCompleted(taskId, sSubtaskId, targetCompleted);
                }
                if (typeof window.TempoEmergencyFlow.setConfirmedPlan === 'function') {
                    window.TempoEmergencyFlow.setConfirmedPlan(plan);
                }
            }

            // 5. Persist to TempoPlanStore
            if (window.TempoPlanStore) {
                if (typeof window.TempoPlanStore.updateTaskState === 'function') {
                    await window.TempoPlanStore.updateTaskState(taskId, {
                        subtasks: matchedTask.subtasks
                    });
                }
                if (sSubtaskId !== 'default' && typeof window.TempoPlanStore.updateSubtaskState === 'function') {
                    await window.TempoPlanStore.updateSubtaskState(taskId, sSubtaskId, {
                        completed: targetCompleted
                    });
                }
                if (typeof window.TempoPlanStore.saveActivePlan === 'function') {
                    await window.TempoPlanStore.saveActivePlan('emergency', plan);
                }
            }

            // 6. Sync with Break Task popup and Plan Workspace if open
            if (window.TempoUrmodeFlow && typeof window.TempoUrmodeFlow.refreshBreakTaskSubtasks === 'function') {
                window.TempoUrmodeFlow.refreshBreakTaskSubtasks(taskId);
            }
            if (window.TempoPlanWorkspace && typeof window.TempoPlanWorkspace.render === 'function') {
                const wsScreen = document.getElementById('screen-plan-workspace');
                if (wsScreen && !wsScreen.classList.contains('hidden')) {
                    window.TempoPlanWorkspace.render();
                }
            }

            // 7. Refresh Urmode dashboard UI
            renderActiveModeHome();
            return true;
        } catch (err) {
            console.error("[TempoMode] Subtask completion failed:", err);
            renderActiveModeHome();
            return false;
        }
    }

    async function markOverdueTaskDone(taskId) {
        return setTaskCompletionStatus(taskId, true, { isOverdue: true });
    }

    let pendingClearOverdueTaskId = null;
    let isClearOverdueSubmitting = false;

    function promptClearOverdueTask(taskId) {
        pendingClearOverdueTaskId = taskId;
        let modal = document.getElementById('modal-mode-clear-task-confirm');
        if (!modal) {
            modal = document.createElement('div');
            modal.id = 'modal-mode-clear-task-confirm';
            modal.className = 'fixed inset-0 z-50 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4';
            modal.setAttribute('role', 'dialog');
            modal.setAttribute('aria-modal', 'true');
            modal.setAttribute('aria-labelledby', 'mode-clear-task-title');
            modal.onclick = function(e) {
                if (e.target === modal) closeClearOverdueTaskModal();
            };
            modal.innerHTML = `
                <div class="tempo-card bg-white border border-[#EAE4DF] rounded-3xl p-6 sm:p-7 space-y-5 shadow-2xl max-w-md w-full relative">
                    <button type="button"
                            onclick="window.TempoMode.closeClearOverdueTaskModal()"
                            class="absolute top-5 right-5 text-gray-400 hover:text-gray-700 text-lg transition cursor-pointer"
                            title="Close"
                            aria-label="Close">✕</button>
                    <div class="space-y-2 pr-6">
                        <h3 id="mode-clear-task-title" class="font-heading text-lg sm:text-xl font-bold text-[#202124]">Clear this task?</h3>
                        <p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed">
                            This task will be removed from your Working Plan. This action cannot be undone.
                        </p>
                    </div>
                    <div class="flex items-center justify-end space-x-3 pt-2">
                        <button type="button"
                                onclick="window.TempoMode.closeClearOverdueTaskModal()"
                                class="px-4 py-2 sm:px-5 sm:py-2.5 rounded-xl text-xs sm:text-sm font-semibold text-stone-600 hover:text-stone-900 border border-transparent hover:bg-stone-50 transition cursor-pointer">
                            Cancel
                        </button>
                        <button type="button"
                                id="btn-confirm-clear-overdue-task"
                                onclick="window.TempoMode.executeClearOverdueTask()"
                                class="px-4 py-2 sm:px-5 sm:py-2.5 rounded-xl text-xs sm:text-sm font-bold bg-[#C53B27] hover:bg-[#B03422] text-white shadow-sm transition cursor-pointer inline-flex items-center justify-center">
                            Clear task
                        </button>
                    </div>
                </div>
            `;
            document.body.appendChild(modal);
        } else {
            modal.classList.remove('hidden');
        }
    }

    function closeClearOverdueTaskModal() {
        if (isClearOverdueSubmitting) return;
        const modal = document.getElementById('modal-mode-clear-task-confirm');
        if (modal) modal.classList.add('hidden');
        pendingClearOverdueTaskId = null;
    }

    async function executeClearOverdueTask() {
        if (isClearOverdueSubmitting) return;
        const taskId = pendingClearOverdueTaskId;
        if (!taskId) {
            closeClearOverdueTaskModal();
            return;
        }

        isClearOverdueSubmitting = true;
        const confirmBtn = document.getElementById('btn-confirm-clear-overdue-task');
        if (confirmBtn) {
            confirmBtn.disabled = true;
            confirmBtn.classList.add('opacity-50', 'cursor-not-allowed');
        }

        try {
            await executeClearOverdueTaskAction(taskId);
            closeClearOverdueTaskModal();
        } finally {
            isClearOverdueSubmitting = false;
            if (confirmBtn) {
                confirmBtn.disabled = false;
                confirmBtn.classList.remove('opacity-50', 'cursor-not-allowed');
            }
        }
    }

    async function executeClearOverdueTaskAction(taskId) {
        if (isTaskActionSubmitting) return;
        isTaskActionSubmitting = true;
        try {
            const activeStorePlan = window.TempoPlanStore && typeof window.TempoPlanStore.getActivePlan === 'function'
                ? window.TempoPlanStore.getActivePlan('emergency')
                : null;
            const flowPlan = window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.getConfirmedPlan === 'function'
                ? window.TempoEmergencyFlow.getConfirmedPlan()
                : null;

            const plan = (activeStorePlan && ((Array.isArray(activeStorePlan.plannedTasks) && activeStorePlan.plannedTasks.length > 0) || (Array.isArray(activeStorePlan.tasks) && activeStorePlan.tasks.length > 0)))
                ? activeStorePlan
                : (flowPlan || activeStorePlan);

            if (!plan) throw new Error("No active Working Plan found.");
            const sTaskId = String(taskId);

            // Remove from plannedTasks
            if (Array.isArray(plan.plannedTasks)) {
                const idx = plan.plannedTasks.findIndex(pt => pt.task && String(pt.task.id) === sTaskId);
                if (idx !== -1) {
                    plan.plannedTasks.splice(idx, 1);
                }
            }
            // Remove from unarrangedTasks
            if (Array.isArray(plan.unarrangedTasks)) {
                const uIdx = plan.unarrangedTasks.findIndex(u => String(u && u.task ? u.task.id : u.id) === sTaskId);
                if (uIdx !== -1) {
                    plan.unarrangedTasks.splice(uIdx, 1);
                }
            }
            // Remove from tasks array
            if (Array.isArray(plan.tasks)) {
                plan.tasks = plan.tasks.filter(t => t && String(t.id) !== sTaskId);
            }

            // Sync with TempoEmergencyFlow
            if (window.TempoEmergencyFlow) {
                if (typeof window.TempoEmergencyFlow.setConfirmedPlan === 'function') {
                    window.TempoEmergencyFlow.setConfirmedPlan(plan);
                }
                if (typeof window.TempoEmergencyFlow.recalculateTimelineSlotsPreservingOrder === 'function') {
                    window.TempoEmergencyFlow.recalculateTimelineSlotsPreservingOrder();
                }
            }

            // Persist updated plan
            if (window.TempoPlanStore && typeof window.TempoPlanStore.saveActivePlan === 'function') {
                await window.TempoPlanStore.saveActivePlan('emergency', plan);
            }

            if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                window.TempoApp.showToast("Overdue task cleared from your Working Plan.");
            }

            renderActiveModeHome();
        } catch (err) {
            console.error("[TempoMode] Failed to clear overdue task:", err);
            if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                window.TempoApp.showToast("Failed to remove task. Please try again.", 4000);
            }
        } finally {
            isTaskActionSubmitting = false;
        }
    }

    async function clearOverdueTask(taskId) {
        promptClearOverdueTask(taskId);
    }

    function showTomorrowTaskInCard() {
        sessionFlags.viewingTomorrowTask = true;
        sessionFlags.restingForToday = false;
        renderActiveModeHome();
    }

    function setRestingForToday(isResting = true) {
        sessionFlags.restingForToday = isResting;
        sessionFlags.viewingTomorrowTask = false;
        renderActiveModeHome();
    }

    // =========================================================================
    // HELPER & VALIDATION UTILITIES
    // =========================================================================

    function getTodayISOString() {
        return getLocalTodayISO();
    }

    function checkIsTodayPlannedTimeEnded(availabilityDays, todayStr) {
        const todayDay = availabilityDays.find(d => d.date === todayStr);
        if (!todayDay || !todayDay.blocks || todayDay.blocks.length === 0) return false;

        const now = new Date();
        const currentMin = (now.getHours() * 60) + now.getMinutes();

        let latestEndMin = 0;
        todayDay.blocks.forEach(b => {
            if (b.end) {
                const [h, m] = b.end.split(':').map(Number);
                const endMin = (h * 60) + (m || 0);
                if (endMin > latestEndMin) latestEndMin = endMin;
            }
        });

        return latestEndMin > 0 && currentMin > latestEndMin;
    }

    function checkNeedsAttentionIssues(confirmedPlan, todayStr) {
        const issues = [];
        if (!confirmedPlan || !confirmedPlan.plannedTasks) return issues;

        confirmedPlan.plannedTasks.forEach(pt => {
            const task = pt.task;
            if (task.completed) return;

            // Issue 1: Deadline conflict
            if (pt.hasDeadlineConflict) {
                issues.push({
                    title: task.name,
                    message: `Due ${formatHumanDeadline(task.deadlineDate, task.deadlineTime)}, but current schedule places completion past this deadline.`
                });
            }

            // Issue 2: Capacity conflict
            if (pt.isOverCapacity) {
                issues.push({
                    title: task.name,
                    message: `Scheduled workload exceeds the available time blocks for ${pt.dayLabel || 'this day'}.`
                });
            }

            // Issue 3: Missing estimate relevant to plan
            if (task.isUnknownDuration && !task.isLongTerm) {
                issues.push({
                    title: task.name,
                    message: "Duration was not estimated, so total schedule feasibility cannot be guaranteed."
                });
            }
        });

        return issues;
    }

    function formatHumanDeadline(dateStr, timeStr) {
        if (window.TempoI18n && typeof window.TempoI18n.formatDeadline === 'function') {
            return window.TempoI18n.formatDeadline(dateStr, timeStr);
        }
        if (!dateStr) return 'No fixed deadline';
        try {
            const date = new Date(`${dateStr}T${timeStr || '23:59'}`);
            return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) + (timeStr ? ` at ${timeStr}` : '');
        } catch (e) {
            return `${dateStr} ${timeStr || ''}`;
        }
    }

    function escapeHTML(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    return {
        MODES,
        init,
        getActiveContext,
        hasActiveContext,
        getSourceContext,
        setSourceContext,
        getOriginatingMode,
        setOriginatingMode,
        clearOriginatingMode,
        getActiveSharedTool,
        getPendingIntent,
        setPendingIntent,
        clearPendingIntent,
        transitionContext,
        requestContext,
        openUcheck,
        returnToSourceContext,
        resolveActiveDashboardContext,
        navigateToActiveDashboard,
        getMode,
        getCurrentMode: getMode,
        getPendingMode,
        hasPendingMode,
        hasPendingIntent,
        getModeDisplayName,
        requestMode,
        handleAuthSuccess,
        handleAuthCancel,
        handleSignOut,
        setMode,
        selectModeOption,
        renderShellIndicator,
        openChangeModeModal,
        closeChangeModeModal,
        openHelpSelectionModal,
        closeHelpSelectionModal,
        toggleModeDropdown,
        toggleNavbarModeDropdown,
        closeAllModeDropdowns,
        selectModeFromDropdown,
        syncModeSelectorDOM,
        renderEmodeHome,
        renderEmodePrimarySection,
        renderRmodeHome,
        renderUmodeHome,
        renderDmodeHome,
        renderEntryHome,
        renderEntryHomeHTML,
        getUserPersistedActiveContext,
        hasEstablishedContext,
        renderDmodeModeSwitchEntry,
        restoreDefaultHome,
        renderActiveModeHome,
        applyModeVisibility,
        toggleDmodeTask,
        toggleDmodeSubtask,
        toggleDmodeSubtasksExpanded,
        startDmodeFocus,
        startDmodeTaskFocus,
        openPlanWorkspace,
        getSharedPlanTodayTasks,
        getSelfCheckState,
        setSelfCheckState,
        handleRecoveryIntroSetupClick,
        handleAddTrackingDirectClick,
        handleSelfCheckSetupClick,
        handleSelfCheckAction,
        handleStreakCardCheckin,
        refreshStreakCardIfPresent,
        submitUmodeSelfCheckValue,
        skipUmodeCurrentSelfCheck,
        resetUmodeSkippedTrackers,
        handleUmodeSliderInput,
        handleUmodeSliderChange,
        handleUmodeTrackPointer,
        confirmUmodePercentage,
        confirmUmodeQuantity,
        getUmodeSkippedTrackers,
        submitRmodeSelfCheckValue,
        skipRmodeCurrentSelfCheck,
        submitRmodeQuantityValue,
        resetRmodeSkippedTrackers,
        openStrack,
        showStressCheckScreen,
        getDestinationDisplayName,
        isValidPendingIntent,
        getRecentlyState,
        setRecentlyState,
        renderRecentlyCard,
        checkIsWeeklyReviewReady,
        setWeeklyReviewReady,
        dismissWeeklyReviewNotice,
        dismissRecoveryIntro,
        setTaskCompletionStatus,
        toggleTaskCompletion,
        startTaskFocus,
        stopForToday,
        keepWorkingToday,
        dismissStaleWarning,
        getSafeGreetingInfo,
        handleCardTaskComplete,
        setSubtaskCompleted,
        handleSubtaskComplete: setSubtaskCompleted,
        promptClearOverdueTask,
        closeClearOverdueTaskModal,
        executeClearOverdueTask,
        clearOverdueTask,
        markOverdueTaskDone,
        showTomorrowTaskInCard,
        setRestingForToday,
        updateNavbarForMode,
        getActiveHomeState: () => currentActiveHomeState,
        syncUmodeCreateNotesAlignment,
        syncRmodeSelfCheckAlignment,
        renderEmodeCreateNotesCard,
        renderRecoveryNoteCard,
        refreshNotesCardIfPresent,
        getUmodeDayNotesForToday,
        getRmodeTaskData,
        persistRmodePlanData,
        openRmodeTaskDetailModal,
        closeRmodeTaskDetailModal,
        isRmodeTaskDetailModalOpen,
        renderRmodeTaskDetailModalHTML,
        renderRmodeTaskDetailModalDOM,
        toggleRmodeDetailTitleEdit,
        saveRmodeDetailTitleEdit,
        toggleRmodeDetailDeadlineEdit,
        saveRmodeDetailDeadlineEdit,
        toggleRmodeDetailNoteEdit,
        saveRmodeDetailNote,
        deleteRmodeDetailNote,
        toggleRmodeDetailTaskComplete,
        toggleRmodeDetailSubtask,
        toggleRmodeDetailAddSubtask,
        addRmodeDetailSubtask,
        removeRmodeDetailSubtask,
        toggleRmodeDetailSubtaskEdit,
        saveRmodeDetailSubtaskTitle,
        toggleRmodeDetailLabelMenu,
        setRmodeDetailTaskLabel,
        promptClearRmodeTask,
        handleRmodeTaskFocus,
        handleRmodeTaskReschedule,
        // URmode Task Detail Modal API
        getUrmodeActivePlan,
        getUrmodeTaskData,
        persistUrmodePlanData,
        openUrmodeTaskDetailModal,
        closeUrmodeTaskDetailModal,
        isUrmodeTaskDetailModalOpen,
        renderUrmodeTaskDetailModalHTML,
        renderUrmodeTaskDetailModalDOM,
        toggleUrmodeDetailTitleEdit,
        saveUrmodeDetailTitleEdit,
        toggleUrmodeDetailDeadlineEdit,
        saveUrmodeDetailDeadlineEdit,
        toggleUrmodeDetailNoteEdit,
        saveUrmodeDetailNote,
        deleteUrmodeDetailNote,
        toggleUrmodeDetailTaskComplete,
        toggleUrmodeDetailSubtask,
        toggleUrmodeDetailAddSubtask,
        addUrmodeDetailSubtask,
        removeUrmodeDetailSubtask,
        toggleUrmodeDetailSubtaskEdit,
        saveUrmodeDetailSubtaskTitle,
        toggleUrmodeDetailLabelMenu,
        setUrmodeDetailTaskLabel,
        promptClearUrmodeTask,
        handleUrmodeTaskFocus,
        handleUrmodeTaskReschedule,
        EPLAN_STATES,
        formatScheduledDateLabel,
        isTaskOverdue,
        isTaskMissedSchedule,
        getTaskState,
        isMissedSchedulePromptDismissed,
        dismissMissedSchedulePrompt,
        clearMissedScheduleDismissal,
        rescheduleMissedTask,
        keepCurrentSchedule,
        markMissedTaskDone,
        getLocalTodayISO
    };
})();

document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        if (window.TempoMode && typeof window.TempoMode.isUrmodeTaskDetailModalOpen === 'function' && window.TempoMode.isUrmodeTaskDetailModalOpen()) {
            window.TempoMode.closeUrmodeTaskDetailModal();
            return;
        }
        if (window.TempoMode && typeof window.TempoMode.isRmodeTaskDetailModalOpen === 'function' && window.TempoMode.isRmodeTaskDetailModalOpen()) {
            window.TempoMode.closeRmodeTaskDetailModal();
            return;
        }
        if (window.TempoMode && typeof window.TempoMode.closeClearOverdueTaskModal === 'function') {
            window.TempoMode.closeClearOverdueTaskModal();
        }
    }
});

window.addEventListener('resize', function() {
    if (window.TempoMode && typeof window.TempoMode.syncUmodeCreateNotesAlignment === 'function') {
        window.TempoMode.syncUmodeCreateNotesAlignment();
    }
    if (window.TempoMode && typeof window.TempoMode.syncRmodeSelfCheckAlignment === 'function') {
        window.TempoMode.syncRmodeSelfCheckAlignment();
    }
});

window.addEventListener('tempo:selfcheck-updated', function() {
    if (window.TempoMode && typeof window.TempoMode.refreshStreakCardIfPresent === 'function') {
        window.TempoMode.refreshStreakCardIfPresent();
    }
    if (window.TempoMode && typeof window.TempoMode.getMode === 'function' && window.TempoMode.getMode() === 'recovery' && typeof window.TempoMode.renderRmodeHome === 'function') {
        window.TempoMode.renderRmodeHome();
    }
    if (window.TempoMode && typeof window.TempoMode.syncRmodeSelfCheckAlignment === 'function') {
        requestAnimationFrame(window.TempoMode.syncRmodeSelfCheckAlignment);
    }
});

window.addEventListener('storage', function(e) {
    if (e && e.key && e.key.includes('tempo_selfcheck')) {
        if (window.TempoMode && typeof window.TempoMode.refreshStreakCardIfPresent === 'function') {
            window.TempoMode.refreshStreakCardIfPresent();
        }
        if (window.TempoMode && typeof window.TempoMode.getMode === 'function' && window.TempoMode.getMode() === 'recovery' && typeof window.TempoMode.renderRmodeHome === 'function') {
            window.TempoMode.renderRmodeHome();
        }
    }
});

window.addEventListener('tempo:note-updated', function() {
    if (window.TempoMode && typeof window.TempoMode.refreshNotesCardIfPresent === 'function') {
        window.TempoMode.refreshNotesCardIfPresent();
    }
});

window.addEventListener('storage', function(e) {
    if (e && e.key && (e.key.includes('note') || e.key.includes('Note'))) {
        if (window.TempoMode && typeof window.TempoMode.refreshNotesCardIfPresent === 'function') {
            window.TempoMode.refreshNotesCardIfPresent();
        }
    }
});

