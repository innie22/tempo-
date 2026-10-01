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

    // Single centralized source of truth for active mode
    let currentMode = MODES.DEFAULT;

    // Remembers intended mode across the authentication gate
    let pendingMode = null;

    // Session-level flags to prevent repeating dismissed alerts
    let sessionFlags = {
        dismissedStaleWarning: false,
        dismissedTimeEndedToday: false
    };

    // Expanded task cards on Default Home
    let dmodeExpandedTaskIds = new Set();

    function hasEstablishedContext() {
        try {
            // 1. Established Urgent Plan / Workspace
            if (window.TempoPlanStore && typeof window.TempoPlanStore.hasActivePlan === 'function') {
                if (window.TempoPlanStore.hasActivePlan('emergency')) return true;
            }
            const savedPlan = localStorage.getItem('tempo_active_plan_emergency') || localStorage.getItem('tempo_confirmed_plan');
            if (savedPlan) {
                const parsed = JSON.parse(savedPlan);
                if (parsed && ((Array.isArray(parsed.plannedTasks) && parsed.plannedTasks.length > 0) || (Array.isArray(parsed.tasks) && parsed.tasks.length > 0))) {
                    return true;
                }
            }

            // 2. Established Recovery Context
            const recConfig = localStorage.getItem('tempo_recovery_selfcheck_config');
            if (recConfig) {
                const parsedRec = JSON.parse(recConfig);
                if (parsedRec && parsedRec.type && parsedRec.type !== 'STATE_A') return true;
            }
            const recNote = localStorage.getItem('tempo_recovery_note_content');
            if (recNote && recNote.trim().length > 0) return true;

            // 3. User explicitly saved an active mode other than default
            const savedMode = localStorage.getItem('tempo_current_mode');
            if (savedMode === MODES.EMERGENCY || savedMode === MODES.RECOVERY || savedMode === MODES.UNCLEAR) {
                return true;
            }
        } catch (e) {}

        return false;
    }

    function init() {
        // Load persisted mode safely from localStorage
        try {
            const savedMode = localStorage.getItem('tempo_current_mode');
            const authState = window.TempoAuth && typeof window.TempoAuth.getAuthState === 'function'
                ? window.TempoAuth.getAuthState()
                : 'AUTH_LOADING';
            const isAuthenticated = window.TempoAuth && !!window.TempoAuth.getCurrentUser();
            const hasActivePlan = window.TempoPlanStore && typeof window.TempoPlanStore.hasActivePlan === 'function' && window.TempoPlanStore.hasActivePlan('emergency');

            if (authState === 'AUTH_LOADING') {
                if (savedMode && Object.values(MODES).includes(savedMode)) {
                    currentMode = savedMode;
                }
            } else if (!isAuthenticated) {
                // Anonymous user -> Always Entry Home (default)
                currentMode = MODES.DEFAULT;
                localStorage.setItem('tempo_current_mode', MODES.DEFAULT);
            } else if (!hasEstablishedContext()) {
                // Authenticated user with no established workspace/context -> Entry Home
                currentMode = MODES.DEFAULT;
                localStorage.setItem('tempo_current_mode', MODES.DEFAULT);
            } else if (savedMode && Object.values(MODES).includes(savedMode)) {
                currentMode = savedMode;
            } else if (hasActivePlan) {
                currentMode = MODES.EMERGENCY;
                localStorage.setItem('tempo_current_mode', MODES.EMERGENCY);
            }

            const savedPending = localStorage.getItem('tempo_pending_mode');
            if (savedPending && Object.values(MODES).includes(savedPending)) {
                pendingMode = savedPending;
            }
        } catch (e) {
            console.warn("[TempoMode] localStorage access error:", e);
        }

        renderShellIndicator();
        bindEvents();

        // Synchronize active mode dashboard with strict mutual exclusivity
        renderActiveModeHome();
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

        // Close mode selector dropdown on outside click
        document.addEventListener('click', (e) => {
            if (!e.target.closest('#home-mode-selector-wrapper') && !e.target.closest('#mode-indicator-shell')) {
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

    function getMode() {
        return currentMode;
    }

    function getPendingMode() {
        return pendingMode;
    }

    function hasPendingMode() {
        return !!pendingMode;
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
     * Request entry into a mode.
     * Enforces the authentication gate for Emode, Rmode, and Umode while
     * keeping Dmode and SOS completely open to anonymous visitors.
     */
    function requestMode(targetMode) {
        if (!Object.values(MODES).includes(targetMode)) {
            targetMode = MODES.DEFAULT;
        }

        // Dmode is always accessible without authentication
        if (targetMode === MODES.DEFAULT) {
            setMode(MODES.DEFAULT);
            if (window.TempoApp) window.TempoApp.navigateTo('today');
            return;
        }

        const isAuthenticated = window.TempoAuth && !!window.TempoAuth.getCurrentUser();

        if (isAuthenticated) {
            // User is already authenticated: enter mode immediately
            setMode(targetMode);
            if (targetMode === MODES.EMERGENCY) {
                const hasPlan = window.TempoPlanStore && typeof window.TempoPlanStore.hasActivePlan === 'function' && window.TempoPlanStore.hasActivePlan('emergency');
                if (hasPlan) {
                    if (window.TempoApp) window.TempoApp.navigateTo('today');
                } else {
                    if (window.TempoApp) window.TempoApp.navigateTo('emergency');
                }
            } else if (targetMode === MODES.RECOVERY) {
                if (window.TempoApp) window.TempoApp.navigateTo('today');
            } else if (targetMode === MODES.UNCLEAR) {
                if (window.TempoApp) window.TempoApp.navigateTo('today');
            }
        } else {
            // Anonymous user: remember intent, show auth gate, do not activate mode yet
            pendingMode = targetMode;
            try {
                localStorage.setItem('tempo_pending_mode', targetMode);
            } catch (e) {}

            updateAuthGateBanners(targetMode);

            if (window.TempoAuth) {
                window.TempoAuth.openSignInModal();
            }

            if (window.TempoApp) {
                window.TempoApp.showToast(`Sign in or create a free account to enter ${getModeDisplayName(targetMode)}.`);
            }
        }
    }

    /**
     * Called immediately after successful sign in or sign up.
     * Continues into the intended mode seamlessly without returning to generic Home.
     */
    function handleAuthSuccess() {
        if (!pendingMode) {
            try {
                pendingMode = localStorage.getItem('tempo_pending_mode');
            } catch (e) {}
        }

        if (pendingMode && Object.values(MODES).includes(pendingMode)) {
            const target = pendingMode;
            pendingMode = null;
            try {
                localStorage.removeItem('tempo_pending_mode');
            } catch (e) {}

            setMode(target, { silent: true });

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
            } else if (target === MODES.UNCLEAR) {
                if (window.TempoApp) {
                    window.TempoApp.navigateTo('today');
                    window.TempoApp.showToast("Welcome! Entering Unclear Mode.");
                }
            }
            return true;
        }

        return false;
    }

    /**
     * Sets the centralized mode state.
     * Persists across reloads without touching or modifying database schema.
     */
    function setMode(newMode, options = {}) {
        if (newMode === 'urgent') {
            newMode = MODES.EMERGENCY;
        }
        if (!Object.values(MODES).includes(newMode)) {
            newMode = MODES.DEFAULT;
        }

        const prevMode = currentMode;
        currentMode = newMode;

        try {
            localStorage.setItem('tempo_current_mode', newMode);
        } catch (e) {}

        // Clear any pending mode once confirmed
        pendingMode = null;
        try {
            localStorage.removeItem('tempo_pending_mode');
        } catch (e) {}

        renderShellIndicator();
        closeChangeModeModal();
        closeAllModeDropdowns();

        if (!options.silent && window.TempoApp) {
            if (newMode === MODES.EMERGENCY) {
                window.TempoApp.showToast("⚡ Urgent Mode active");
            } else if (newMode === MODES.RECOVERY) {
                window.TempoApp.showToast("🌱 Switched to Recovery Mode");
            } else if (newMode === MODES.UNCLEAR) {
                window.TempoApp.showToast("🧭 Switched to Unclear Mode");
            } else if (newMode === MODES.DEFAULT) {
                window.TempoApp.showToast("Returned to Default Tempo. All tasks remain saved.");
            }
        }

        // Synchronize view for active mode dashboard with strict mutual exclusivity
        renderActiveModeHome();

        if (!options.silent && window.TempoApp) {
            window.TempoApp.navigateTo('today');
        }

        if (newMode === MODES.RECOVERY) {
            if (!options.skipSetupCheck && window.TempoRecoverySetup && typeof window.TempoRecoverySetup.shouldShowFirstTimeWelcome === 'function') {
                if (window.TempoRecoverySetup.shouldShowFirstTimeWelcome()) {
                    window.TempoRecoverySetup.open(1);
                }
            }
        }
    }

    // =========================================================================
    // GLOBAL SHELL INDICATOR & MODE SELECTOR DROPDOWNS
    // =========================================================================

    function renderShellIndicator() {
        const shell = document.getElementById('mode-indicator-shell');
        const badge = document.getElementById('mode-badge');
        const icon = document.getElementById('mode-badge-icon');
        const label = document.getElementById('mode-badge-label');

        if (!shell || !badge || !icon || !label) return;

        if (currentMode === MODES.DEFAULT) {
            shell.classList.add('hidden');
            shell.classList.remove('flex');
            return;
        }

        shell.classList.remove('hidden');
        shell.classList.add('flex');

        if (currentMode === MODES.EMERGENCY) {
            badge.className = 'px-2.5 py-1 rounded-full text-xs font-bold bg-[#FFE9DC] text-[#B83D08] flex items-center space-x-1.5 shadow-sm';
            icon.textContent = '⚡';
            label.textContent = window.t ? window.t('modes.urgent.name', {}, 'Urgent Mode') : 'Urgent Mode';
        } else if (currentMode === MODES.RECOVERY) {
            badge.className = 'px-2.5 py-1 rounded-full text-xs font-bold bg-[#EDF7F1] text-[#166545] flex items-center space-x-1.5 shadow-sm';
            icon.textContent = '🌱';
            label.textContent = window.t ? window.t('modes.recovery.name', {}, 'Recovery Mode') : 'Recovery Mode';
        } else if (currentMode === MODES.UNCLEAR) {
            badge.className = 'px-2.5 py-1 rounded-full text-xs font-bold bg-[#FEF7EC] text-[#9A5B13] flex items-center space-x-1.5 shadow-sm';
            icon.textContent = '🧭';
            label.textContent = window.t ? window.t('modes.unclear.name', {}, 'Unclear Mode') : 'Unclear Mode';
        }
    }

    function renderModeDropdownHTML(origin = 'home') {
        const showUrgent = currentMode !== MODES.EMERGENCY;
        const showRecovery = currentMode !== MODES.RECOVERY;
        const showUnclear = currentMode !== MODES.UNCLEAR;
        const showDefault = currentMode !== MODES.DEFAULT;

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

        if (showDefault) {
            itemsHTML += `
                <!-- Divider -->
                <div class="border-t border-[#EAE4DF] my-1.5"></div>

                <!-- Take a break / Default Mode -->
                <button type="button" onclick="window.TempoMode.selectModeFromDropdown('${MODES.DEFAULT}', '${origin}')"
                        class="w-full text-left p-2.5 rounded-xl hover:bg-stone-50 flex items-start justify-between group transition cursor-pointer" role="menuitem">
                    <div class="flex items-start space-x-2.5">
                        <span class="text-base text-stone-500 mt-0.5 leading-none">○</span>
                        <div>
                            <div class="text-xs font-bold text-[#202124] group-hover:text-stone-900 transition-colors">${window.t ? window.t('modes.selector.takeBreak', {}, 'Take a break from modes') : 'Take a break from modes'}</div>
                            <div class="text-[11px] text-[#6F6B68]">${window.t ? window.t('modes.selector.takeBreakDesc', {}, 'Return to the default experience') : 'Return to the default experience'}</div>
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

    function toggleModeDropdown(event) {
        if (event) {
            event.stopPropagation();
            event.preventDefault();
        }
        const dropdown = document.getElementById('home-mode-selector-dropdown');
        if (!dropdown) return;
        const isHidden = dropdown.classList.contains('hidden');
        closeAllModeDropdowns();
        if (isHidden) {
            dropdown.innerHTML = renderModeDropdownHTML('home');
            dropdown.classList.remove('hidden');
            const trigger = document.getElementById('btn-home-mode-selector');
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
        const homeDropdown = document.getElementById('home-mode-selector-dropdown');
        if (homeDropdown) {
            homeDropdown.classList.add('hidden');
            const trigger = document.getElementById('btn-home-mode-selector');
            if (trigger) trigger.setAttribute('aria-expanded', 'false');
        }
        const navDropdown = document.getElementById('navbar-mode-dropdown');
        if (navDropdown) {
            navDropdown.classList.add('hidden');
            const trigger = document.getElementById('btn-mode-indicator-trigger');
            if (trigger) trigger.setAttribute('aria-expanded', 'false');
        }
    }

    function selectModeFromDropdown(targetMode, origin = 'home') {
        closeAllModeDropdowns();
        if (targetMode === currentMode) return;
        requestMode(targetMode);
    }

    function openChangeModeModal() {
        const modal = document.getElementById('modal-change-mode');
        if (!modal) return;

        const optEmergency = document.getElementById('change-mode-opt-emergency');
        const optRecovery = document.getElementById('change-mode-opt-recovery');
        const optUnclear = document.getElementById('change-mode-opt-unclear');
        const optDefault = document.getElementById('change-mode-opt-default');
        const footerBtn = document.getElementById('change-mode-footer-btn');

        if (optEmergency) optEmergency.classList.toggle('hidden', currentMode === MODES.EMERGENCY);
        if (optRecovery) optRecovery.classList.toggle('hidden', currentMode === MODES.RECOVERY);
        if (optUnclear) optUnclear.classList.toggle('hidden', currentMode === MODES.UNCLEAR);
        if (optDefault) optDefault.classList.toggle('hidden', currentMode === MODES.DEFAULT);

        if (footerBtn) {
            footerBtn.textContent = `Stay in ${getModeDisplayName(currentMode)}`;
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

    function selectModeOption(targetMode) {
        closeChangeModeModal();
        if (targetMode === currentMode) return;
        requestMode(targetMode);
    }

    function updateAuthGateBanners(targetMode) {
        document.querySelectorAll('.auth-mode-gate-banner').forEach(banner => {
            const titleEl = banner.querySelector('.auth-mode-gate-title');
            const descEl = banner.querySelector('.auth-mode-gate-desc');

            if (targetMode && targetMode !== MODES.DEFAULT) {
                banner.classList.remove('hidden');
                if (titleEl) titleEl.textContent = `${getModeDisplayName(targetMode)} requires an account`;
                if (descEl) descEl.textContent = `Sign in or register below to save your plan. You will enter ${getModeDisplayName(targetMode)} immediately after.`;
            } else {
                banner.classList.add('hidden');
            }
        });
    }

    // =========================================================================
    // CENTRALIZED MODE DASHBOARD VISIBILITY CONTROLLER
    // Strict mutual exclusivity: exactly one mode dashboard is visible on Home.
    // =========================================================================

    function applyModeVisibility(targetMode) {
        const mode = targetMode || currentMode || MODES.DEFAULT;
        const dmodeBox = document.getElementById('dmode-home-content');
        const emodeBox = document.getElementById('emode-home-content');
        const rmodeBox = document.getElementById('rmode-home-content');
        const umodeBox = document.getElementById('umode-home-content');

        if (dmodeBox) dmodeBox.classList.toggle('hidden', mode !== MODES.DEFAULT);
        if (emodeBox) emodeBox.classList.toggle('hidden', mode !== MODES.EMERGENCY);
        if (rmodeBox) rmodeBox.classList.toggle('hidden', mode !== MODES.RECOVERY);
        if (umodeBox) umodeBox.classList.toggle('hidden', mode !== MODES.UNCLEAR);
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
        const tomorrowStr = tomorrowObj.toISOString().split('T')[0];

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
                                onclick="if (window.TempoRecoverySelfCheck) window.TempoRecoverySelfCheck.openSetup();"
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
                                onclick="if (window.TempoRecoverySelfCheck) window.TempoRecoverySelfCheck.openDailyCheckin(false);"
                                class="btn-primary px-4 py-2 rounded-xl text-xs sm:text-sm font-bold shadow-xs inline-flex items-center space-x-1.5 transition cursor-pointer">
                            <span>Check in</span>
                            <span>→</span>
                        </button>
                        <button type="button" 
                                onclick="if (window.TempoRecoverySelfCheck) window.TempoRecoverySelfCheck.openManage();"
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
                                onclick="if (window.TempoRecoverySelfCheck) { if (typeof window.TempoRecoverySelfCheck.openViewToday === 'function') window.TempoRecoverySelfCheck.openViewToday(); else window.TempoRecoverySelfCheck.openDailyCheckin(true); }"
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
                        <span>See all posts</span>
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

    function renderEntryHomeHTML() {
        const posts = (window.TempoCommunity && typeof window.TempoCommunity.getAllPosts === 'function')
            ? window.TempoCommunity.getAllPosts().slice(0, 2)
            : [];
        const postsCardsHTML = (posts.length > 0 && window.TempoCommunity && typeof window.TempoCommunity.renderPostCardHTML === 'function')
            ? posts.map(p => window.TempoCommunity.renderPostCardHTML(p)).join('')
            : '';

        return `
            <div class="space-y-8 sm:space-y-10" data-tempo-ui="entry-home">
                <!-- ROW 1: DESKTOP 2-COLUMN (PRIMARY ENTRY CARD + COMMUNITY PANEL) -->
                <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 lg:gap-8 items-stretch">
                    <!-- LEFT: Large Primary Entry Card (Substantially wider than right panel) -->
                    <div class="lg:col-span-8 flex flex-col">
                        <div class="relative bg-gradient-to-br from-[#FFF9F5] via-[#FFF3EB] to-[#FFEFE6] border border-[#FFD2BA] rounded-3xl p-7 sm:p-10 lg:p-12 shadow-xs overflow-hidden flex flex-col justify-between flex-1" data-tempo-ui="entry-card-primary">
                            <!-- Subtle warm glowing decorative shape in background (matching screenshot) -->
                            <div class="absolute -right-16 -top-16 w-72 h-72 bg-[#FF6B2C]/10 rounded-full blur-3xl pointer-events-none"></div>
                            <div class="absolute right-4 bottom-0 w-80 h-80 bg-gradient-to-tl from-[#FF6B2C]/15 via-[#FF8A50]/10 to-transparent rounded-full blur-2xl pointer-events-none"></div>

                            <div class="relative z-10 space-y-4 sm:space-y-5">
                                <!-- Small Orange Welcome Eyebrow -->
                                <span class="text-xs sm:text-sm font-extrabold uppercase tracking-wider text-[#FF6B2C] block">
                                    ${window.t ? window.t('modes.default.welcomeEyebrow', {}, 'WELCOME TO TEMPO') : 'WELCOME TO TEMPO'}
                                </span>

                                <!-- Large Dominant Question -->
                                <h1 class="font-heading text-3xl sm:text-4xl lg:text-5xl font-extrabold text-[#202124] tracking-tight leading-tight max-w-xl">
                                    ${window.t ? window.t('modes.default.whatDoYouNeed', {}, 'What do you need right now?') : 'What do you need right now?'}
                                </h1>

                                <!-- Supporting Explanatory Copy -->
                                <p class="text-sm sm:text-base text-[#6F6B68] leading-relaxed max-w-lg">
                                    ${window.t ? window.t('modes.default.explainCopy', {}, 'You don’t need to figure it out alone.<br class="hidden sm:inline"> Tell Tempo your current situation, and we’ll help you find the next step.') : 'You don’t need to figure it out alone.<br class="hidden sm:inline"> Tell Tempo your current situation, and we’ll help you find the next step.'}
                                </p>

                                <!-- Large Orange CTA Button -->
                                <div class="pt-2 sm:pt-3">
                                    <button type="button"
                                            onclick="if (window.TempoMode && window.TempoMode.setMode) { window.TempoMode.setMode('unclear'); } else if (window.TempoMode && window.TempoMode.openChangeModeModal) { window.TempoMode.openChangeModeModal(); }"
                                            class="btn-primary px-7 sm:px-8 py-3.5 sm:py-4 rounded-2xl font-bold text-sm sm:text-base shadow-sm hover:shadow-md transition cursor-pointer inline-flex items-center space-x-2.5">
                                        <span>${window.t ? window.t('modes.default.helpMeStart', {}, 'Help me figure out where to start') : 'Help me figure out where to start'}</span>
                                        <span class="text-base sm:text-lg">→</span>
                                    </button>
                                </div>
                            </div>

                            <!-- Small Supporting Reassurance Row -->
                            <div class="relative z-10 flex flex-wrap items-center gap-x-6 gap-y-2 text-xs font-semibold text-[#6F6B68] pt-6 sm:pt-8">
                                <div class="flex items-center space-x-2">
                                    <svg class="w-4 h-4 text-[#FF6B2C] shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <circle cx="12" cy="12" r="10" stroke-width="2"/>
                                        <polyline points="12 6 12 12 16 14" stroke-width="2"/>
                                    </svg>
                                    <span>${window.t ? window.t('modes.default.takesLessOneMin', {}, 'Takes less than 1 minute') : 'Takes less than 1 minute'}</span>
                                </div>
                                <div class="flex items-center space-x-2">
                                    <svg class="w-4 h-4 text-[#FF6B2C] shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
                                    </svg>
                                    <span>${window.t ? window.t('modes.default.personalizedGuidance', {}, 'Personalized guidance') : 'Personalized guidance'}</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- RIGHT: Tempo Community Panel (Social Peer Posts) -->
                    <div class="lg:col-span-4 flex flex-col">
                        <div class="bg-white border border-[#EAE4DF] rounded-3xl p-5 sm:p-6 shadow-xs flex flex-col justify-between space-y-4 flex-1" data-tempo-ui="entry-community-panel">
                            <!-- Header -->
                            <div class="flex items-center justify-between pb-1 border-b border-[#F0ECE9]">
                                <div class="flex items-center space-x-2">
                                    <div class="w-6 h-6 rounded-lg bg-[#FFE9DC] text-[#FF6B2C] flex items-center justify-center text-xs shrink-0 font-bold">
                                        💬
                                    </div>
                                    <h3 class="font-heading font-bold text-sm sm:text-base text-[#202124]">
                                        ${window.t ? window.t('modes.default.fromCommunity', {}, 'From the Tempo community') : 'From the Tempo community'}
                                    </h3>
                                </div>
                                <button type="button"
                                        onclick="if (window.TempoCommunity && window.TempoCommunity.openCommunityModal) { window.TempoCommunity.openCommunityModal(); }"
                                        class="text-xs font-bold text-[#FF6B2C] hover:text-[#B83D08] flex items-center space-x-1 transition cursor-pointer">
                                    <span>${window.t ? window.t('modes.default.seeAll', {}, 'See all') : 'See all'}</span>
                                    <span>→</span>
                                </button>
                            </div>

                            <!-- Social Peer Posts Container -->
                            <div id="homepage-community-posts-list" class="space-y-3.5 flex-1">
                                ${postsCardsHTML}
                            </div>
                        </div>
                    </div>
                </div>

                <!-- ROW 2: QUICK TOOLS (Spanning Main Content Width) -->
                <div class="space-y-4 pt-2" data-tempo-ui="entry-quick-tools">
                    <div class="flex flex-col sm:flex-row sm:items-end justify-between gap-2">
                        <div>
                            <h2 class="font-heading text-xl sm:text-2xl font-bold text-[#202124]">
                                ${window.t ? window.t('modes.default.quickTools', {}, 'Quick Tools') : 'Quick Tools'}
                            </h2>
                            <p class="text-xs sm:text-sm text-[#6F6B68] mt-0.5">
                                ${window.t ? window.t('modes.default.quickToolsSubtitle', {}, 'Simple tools to help you feel better and get through your day.') : 'Simple tools to help you feel better and get through your day.'}
                            </p>
                        </div>
                        <button type="button"
                                onclick="if (window.TempoApp && window.TempoApp.navigateTo) { window.TempoApp.navigateTo('tools'); }"
                                class="text-xs font-bold text-[#FF6B2C] hover:text-[#B83D08] flex items-center space-x-1 transition cursor-pointer shrink-0 self-start sm:self-auto">
                            <span>${window.t ? window.t('modes.default.viewAllTools', {}, 'View all tools') : 'View all tools'}</span>
                            <span>→</span>
                        </button>
                    </div>

                    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                        <!-- Tool 1: Focus Zone -->
                        <div onclick="if (window.TempoFocusZone && window.TempoFocusZone.openQuickEntry) { window.TempoFocusZone.openQuickEntry(); } else if (window.TempoTriage && window.TempoTriage.launchFocusMode) { window.TempoTriage.launchFocusMode(); }"
                             class="bg-white border border-[#EAE4DF] hover:border-[#FFD2BA] rounded-2xl p-5 shadow-xs transition hover:shadow-sm cursor-pointer flex flex-col justify-between group space-y-4">
                            <div class="space-y-3">
                                <div class="w-10 h-10 rounded-2xl bg-[#FFF3EB] text-[#FF6B2C] flex items-center justify-center text-lg">
                                    ⏰
                                </div>
                                <div>
                                    <h3 class="font-heading font-bold text-sm sm:text-base text-[#202124] group-hover:text-[#FF6B2C] transition-colors">
                                        ${window.t ? window.t('modes.default.focusZone', {}, 'Focus Zone') : 'Focus Zone'}
                                    </h3>
                                    <p class="text-xs text-[#6F6B68] leading-relaxed mt-1">
                                        ${window.t ? window.t('modes.default.focusZoneDesc', {}, 'Focus with intentional breaks. Default 45 min focus / 15 min rest.') : 'Focus with intentional breaks. Default 45 min focus / 15 min rest.'}
                                    </p>
                                </div>
                            </div>
                            <div class="flex justify-end pt-1">
                                <div class="w-7 h-7 rounded-full bg-stone-100 group-hover:bg-[#FFE9DC] text-stone-600 group-hover:text-[#B83D08] flex items-center justify-center text-xs transition">
                                    →
                                </div>
                            </div>
                        </div>

                        <!-- Tool 2: Breathing -->
                        <div onclick="if (window.TempoBreathing && window.TempoBreathing.openModal) { window.TempoBreathing.openModal(); } else if (window.TempoTriage && window.TempoTriage.openBoxBreathingModal) { window.TempoTriage.openBoxBreathingModal(); }"
                             class="bg-white border border-[#EAE4DF] hover:border-[#CDE9DA] rounded-2xl p-5 shadow-xs transition hover:shadow-sm cursor-pointer flex flex-col justify-between group space-y-4">
                            <div class="space-y-3">
                                <div class="w-10 h-10 rounded-2xl bg-[#EDF7F1] text-[#166545] flex items-center justify-center text-lg">
                                    💨
                                </div>
                                <div>
                                    <h3 class="font-heading font-bold text-sm sm:text-base text-[#202124] group-hover:text-[#166545] transition-colors">
                                        ${window.t ? window.t('modes.default.breathing', {}, 'Breathing') : 'Breathing'}
                                    </h3>
                                    <p class="text-xs text-[#6F6B68] leading-relaxed mt-1">
                                        ${window.t ? window.t('modes.default.breathingDesc', {}, 'A quick breathing exercise to calm your mind.') : 'A quick breathing exercise to calm your mind.'}
                                    </p>
                                </div>
                            </div>
                            <div class="flex justify-end pt-1">
                                <div class="w-7 h-7 rounded-full bg-stone-100 group-hover:bg-[#DDF0E5] text-stone-600 group-hover:text-[#166545] flex items-center justify-center text-xs transition">
                                    →
                                </div>
                            </div>
                        </div>

                        <!-- Tool 3: Quick Stress Relief -->
                        <div onclick="if (window.TempoStressRelief && window.TempoStressRelief.openModal) { window.TempoStressRelief.openModal(); } else if (window.TempoTriage && window.TempoTriage.openQuickReliefModal) { window.TempoTriage.openQuickReliefModal(); }"
                             class="bg-white border border-[#EAE4DF] hover:border-[#FFD2BA] rounded-2xl p-5 shadow-xs transition hover:shadow-sm cursor-pointer flex flex-col justify-between group space-y-4">
                            <div class="space-y-3">
                                <div class="w-10 h-10 rounded-2xl bg-[#FFF9F5] text-[#FF6B2C] flex items-center justify-center text-lg">
                                    ⚡
                                </div>
                                <div>
                                    <h3 class="font-heading font-bold text-sm sm:text-base text-[#202124] group-hover:text-[#FF6B2C] transition-colors">
                                        ${window.t ? window.t('modes.default.quickStressRelief', {}, 'Quick Stress Relief') : 'Quick Stress Relief'}
                                    </h3>
                                    <p class="text-xs text-[#6F6B68] leading-relaxed mt-1">
                                        ${window.t ? window.t('modes.default.quickStressReliefDesc', {}, 'Feel overwhelmed? Try a simple action to ease stress in a few minutes.') : 'Feel overwhelmed? Try a simple action to ease stress in a few minutes.'}
                                    </p>
                                </div>
                            </div>
                            <div class="flex justify-end pt-1">
                                <div class="w-7 h-7 rounded-full bg-stone-100 group-hover:bg-[#FFE9DC] text-stone-600 group-hover:text-[#B83D08] flex items-center justify-center text-xs transition">
                                    →
                                </div>
                            </div>
                        </div>

                        <!-- Tool 4: Self-check -->
                        <div onclick="if (window.TempoRecoverySetup && window.TempoRecoverySetup.open) { window.TempoRecoverySetup.open(1); } else if (window.TempoRecoverySelfCheck && window.TempoRecoverySelfCheck.openSetup) { window.TempoRecoverySelfCheck.openSetup(); }"
                             class="bg-white border border-[#EAE4DF] hover:border-stone-300 rounded-2xl p-5 shadow-xs transition hover:shadow-sm cursor-pointer flex flex-col justify-between group space-y-4">
                            <div class="space-y-3">
                                <div class="w-10 h-10 rounded-2xl bg-stone-100 text-stone-700 flex items-center justify-center text-lg">
                                    📊
                                </div>
                                <div>
                                    <h3 class="font-heading font-bold text-sm sm:text-base text-[#202124] group-hover:text-stone-900 transition-colors">
                                        ${window.t ? window.t('modes.default.selfCheck', {}, 'Self-check') : 'Self-check'}
                                    </h3>
                                    <p class="text-xs text-[#6F6B68] leading-relaxed mt-1">
                                        ${window.t ? window.t('modes.default.selfCheckDesc', {}, 'Track your stress signals and wellbeing habits.') : 'Track your stress signals and wellbeing habits.'}
                                    </p>
                                </div>
                            </div>
                            <div class="flex justify-end pt-1">
                                <div class="w-7 h-7 rounded-full bg-stone-100 group-hover:bg-stone-200 text-stone-600 group-hover:text-stone-900 flex items-center justify-center text-xs transition">
                                    →
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
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
        if (window.TempoPlanWorkspace && typeof window.TempoPlanWorkspace.toggleSubtask === 'function') {
            window.TempoPlanWorkspace.toggleSubtask(taskId, subtaskId);
        } else if (window.TempoPlanStore && typeof window.TempoPlanStore.getActivePlan === 'function') {
            const plan = window.TempoPlanStore.getActivePlan('emergency');
            const pt = plan?.plannedTasks?.find(item => item.task && item.task.id === taskId);
            if (pt && pt.task && Array.isArray(pt.task.subtasks)) {
                const sub = pt.task.subtasks.find(s => s.id === subtaskId);
                if (sub) {
                    sub.completed = !sub.completed;
                    window.TempoPlanStore.saveActivePlan('emergency', plan);
                }
            }
        }
        renderActiveModeHome();
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
        const confirmedPlan = (activeStorePlan && activeStorePlan.plannedTasks && activeStorePlan.plannedTasks.length > 0)
            ? activeStorePlan
            : ((window.TempoEmergencyFlow && window.TempoEmergencyFlow.getConfirmedPlan) ? window.TempoEmergencyFlow.getConfirmedPlan() : null);

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
            const allPlanned = confirmedPlan.plannedTasks;
            const allCompleted = allPlanned.every(pt => pt.task && pt.task.completed === true);

            if (allCompleted) {
                activeHomeState = 'PLAN_COMPLETE';
            } else {
                // Check for stale planned tasks from past dates
                const staleTasks = allPlanned.filter(pt => {
                    return pt.dayDate && pt.dayDate < todayStr && (!pt.task || !pt.task.completed);
                });

                if (staleTasks.length > 0 && !sessionFlags.dismissedStaleWarning) {
                    activeHomeState = 'PLAN_STALE';
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

        // Render appropriate view according to state with stable ~65 / 35 outer shell
        emodeBox.innerHTML = `
            <div class="relative space-y-5" data-tempo-ui="urgent-home-shell">
                ${renderEmodeHeader()}
                <div class="urgent-home-main-grid">
                    <!-- LEFT COLUMN (~65%) -->
                    <div class="urgent-left-col" data-tempo-ui="urgent-left-col">
                        ${renderEmodePrimarySection(activeHomeState, { confirmedPlan, currentStage, availabilityDays, todayStr, greetingInfo })}
                        ${renderSupportRowHTML()}
                    </div>
                    <!-- RIGHT COLUMN (~35%) -->
                    <div class="urgent-right-col bg-white border border-[#EAE4DF] rounded-3xl p-6 sm:p-7 space-y-5 shadow-xs flex flex-col justify-between" data-tempo-ui="urgent-plan-today">
                        ${renderEmodeRightCol(activeHomeState, { confirmedPlan, todayStr, currentStage })}
                    </div>
                </div>
                ${renderTempoPostsSection()}
            </div>
        `;

        // Trigger community posts preview sync for urgent feed
        if (window.TempoCommunity && typeof window.TempoCommunity.renderUrgentPreview === 'function') {
            window.TempoCommunity.renderUrgentPreview();
        }
    }

    function renderEmodeHeader() {
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

        return `
            <div class="relative pb-1">
                <!-- Top Mode Selector & Date Row -->
                <div class="flex items-center justify-between gap-4">
                    <!-- Anchored Mode Selector Dropdown -->
                    <div id="home-mode-selector-wrapper" class="relative inline-block text-left">
                        <button id="btn-home-mode-selector" 
                                type="button" 
                                data-tempo-ui="mode-selector-btn"
                                onclick="window.TempoMode.toggleModeDropdown(event)" 
                                class="px-3.5 py-1.5 rounded-full text-xs font-bold bg-[#FFE9DC] text-[#B83D08] hover:bg-[#FFDFC9] border border-[#FFD2BA] transition flex items-center space-x-1.5 shadow-xs cursor-pointer focus:outline-none focus:ring-2 focus:ring-[#FF6B2C] focus:ring-offset-1"
                                aria-haspopup="true"
                                aria-expanded="false"
                                title="Switch Tempo Mode">
                            <span>⚡</span>
                            <span class="font-extrabold">${window.t ? window.t('modes.urgent.name', {}, 'Urgent Mode') : 'Urgent Mode'}</span>
                            <span class="text-[10px] ml-0.5 opacity-80">▾</span>
                        </button>
                        <div id="home-mode-selector-dropdown" class="hidden absolute left-0 mt-2 w-72 sm:w-80 bg-white rounded-2xl shadow-xl border border-[#EAE4DF] z-50 overflow-hidden" role="menu"></div>
                    </div>

                    <!-- Date Display -->
                    <div class="text-xs font-semibold text-[#6F6B68]">
                        ${escapeHTML(formattedDate)}
                    </div>
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
            'breakdown': 'Step Breakdown',
            'handoff': 'Start Working Handoff'
        };

        const currentStageTitle = stageNames[currentStage] || 'Urgent Setup';

        return `
            <div class="bg-gradient-to-br from-[#FFF9F5] via-[#FFF3EB] to-[#FFEFE6] border-2 border-[#FFD2BA] rounded-3xl p-6 sm:p-7 space-y-4 shadow-sm relative overflow-hidden">
                <div class="absolute -right-8 -top-8 w-32 h-32 bg-[#FF6B2C]/5 rounded-full blur-2xl pointer-events-none"></div>
                <div class="relative z-10 space-y-1.5">
                    <span class="px-3 py-1 rounded-full text-[11px] font-extrabold bg-[#FFE9DC] text-[#B83D08] uppercase tracking-wider">
                        ${window.t ? window.t('modes.urgent.yourUrgentPlanUpper', {}, 'YOUR URGENT PLAN') : 'YOUR URGENT PLAN'}
                    </span>
                    <div class="text-xs sm:text-sm font-semibold text-[#6F6B68] pt-1">
                        ${escapeHTML(greetingInfo ? greetingInfo.greetingText : 'Hi there 👋')}
                    </div>
                    <h3 class="font-heading text-xl sm:text-2xl font-extrabold text-[#202124]">
                        ${window.t ? window.t('modes.urgent.statePlanIncomplete', {}, "You're still setting up your plan.") : "You're still setting up your plan."}
                    </h3>
                    <p class="text-xs sm:text-sm text-[#6F6B68] max-w-lg leading-relaxed">
                        ${window.t ? window.t('modes.urgent.statePlanIncompleteDesc', {}, 'Your urgent plan setup is in progress.') : 'Your urgent plan setup is in progress at step:'} <strong class="text-[#202124]">${escapeHTML(currentStageTitle)}</strong>.
                    </p>
                </div>

                <div class="relative z-10 pt-1 flex flex-wrap items-center gap-3">
                    <button onclick="window.TempoApp.navigateTo('emergency'); window.TempoEmergencyFlow.goToStage('${currentStage}');"
                            class="btn-primary px-5 py-2.5 rounded-xl font-bold text-xs sm:text-sm shadow-sm inline-flex items-center space-x-2 transition cursor-pointer">
                        <span>${window.t ? window.t('modes.urgent.continueBuilding', {}, 'Continue building my plan') : 'Continue building my plan'}</span>
                        <span>→</span>
                    </button>
                    <button onclick="window.TempoMode.openChangeModeModal()" 
                            class="px-4 py-2.5 rounded-xl border border-[#EAE4DF] text-xs font-semibold text-gray-700 bg-white hover:bg-stone-50 transition cursor-pointer">
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
        const totalTasks = confirmedPlan?.plannedTasks?.length || 0;

        return `
            <div class="bg-gradient-to-br from-[#FFF9F5] via-[#FFF3EB] to-[#FFEFE6] border-2 border-[#FFD2BA] rounded-3xl p-6 sm:p-7 space-y-5 text-center shadow-sm relative overflow-hidden">
                <div class="absolute -right-8 -top-8 w-32 h-32 bg-[#FF6B2C]/5 rounded-full blur-2xl pointer-events-none"></div>
                <div class="relative z-10 w-12 h-12 bg-white/80 text-[#166545] border border-[#CDE9DA] rounded-2xl flex items-center justify-center mx-auto text-2xl shadow-xs">
                    🎉
                </div>
                <div class="relative z-10 space-y-1.5 max-w-md mx-auto">
                    <span class="text-[11px] font-extrabold uppercase tracking-widest text-[#166545]">${window.t ? window.t('modes.urgent.completed', {}, 'ACUTE CRISIS CLEARED') : 'ACUTE CRISIS CLEARED'}</span>
                    <div class="text-xs sm:text-sm font-semibold text-[#6F6B68]">
                        ${escapeHTML(greetingInfo ? greetingInfo.greetingText : 'Hi there 👋')}
                    </div>
                    <h3 class="font-heading text-xl sm:text-2xl font-extrabold text-[#202124]">
                        ${window.t ? window.t('modes.urgent.statePlanComplete', {}, 'Your Urgent Plan is complete.') : 'Your Urgent Plan is complete.'}
                    </h3>
                    <p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed">
                        ${window.t ? window.t('modes.urgent.statePlanCompleteDesc', {}, 'All tasks in this urgent plan are finished.') : 'All tasks in this urgent plan are finished.'}
                    </p>
                </div>

                <!-- Mode Recommendation Suggestion (Never forced) -->
                <div class="relative z-10 p-3.5 bg-white/90 border border-[#FFD2BA] rounded-2xl max-w-md mx-auto text-left flex items-start space-x-3 text-xs text-[#166545]">
                    <span class="text-base">🌱</span>
                    <div class="space-y-0.5">
                        <p class="font-bold">Tempo Recommendation:</p>
                        <p class="text-[#202124] leading-relaxed">Your workload has eased up. Shifting toward <strong>${window.t ? window.t('modes.recovery.name', {}, 'Recovery Mode') : 'Recovery Mode'}</strong> can help you restore energy and rebuild a sustainable pace.</p>
                    </div>
                </div>

                <div class="relative z-10 pt-1 flex flex-col sm:flex-row items-center justify-center gap-2.5">
                    <button onclick="window.TempoMode.setMode('recovery')" 
                            class="btn-primary px-5 py-2.5 rounded-xl font-bold text-xs sm:text-sm shadow-sm transition cursor-pointer">
                        ${window.t ? window.t('modes.urgent.shiftToRecovery', {}, 'Shift to Recovery Mode →') : 'Shift to Recovery Mode →'}
                    </button>
                    <button onclick="window.TempoMode.openChangeModeModal()" 
                            class="px-4 py-2.5 rounded-xl border border-[#EAE4DF] text-xs font-semibold text-gray-700 bg-white hover:bg-stone-50 transition cursor-pointer">
                        ${window.t ? window.t('modes.selector.switchMode', {}, 'Change mode') : 'Change mode'}
                    </button>
                    <button onclick="window.TempoApp.showToast('Remaining in Urgent Mode.')" 
                            class="px-3 py-2 text-xs text-[#6F6B68] hover:text-[#202124] underline cursor-pointer">
                        ${window.t ? window.t('modes.urgent.stayInUrgent', {}, 'Stay in Urgent Mode') : 'Stay in Urgent Mode'}
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
            return pt.dayDate && pt.dayDate < todayStr && (!pt.task || !pt.task.completed);
        });

        return `
            <div class="bg-gradient-to-br from-[#FFF9F5] via-[#FFF3EB] to-[#FFEFE6] border-2 border-[#FFD2BA] rounded-3xl p-5 sm:p-6 space-y-4 shadow-sm relative overflow-hidden">
                <div class="absolute -right-8 -top-8 w-32 h-32 bg-[#FF6B2C]/5 rounded-full blur-2xl pointer-events-none"></div>
                <div class="relative z-10 flex items-start space-x-3.5">
                    <span class="text-2xl mt-0.5">⚠️</span>
                    <div class="space-y-1">
                        <span class="text-[11px] font-bold uppercase tracking-wider text-[#B83D08]">SCHEDULE UPDATE NEEDED</span>
                        <div class="text-xs sm:text-sm font-semibold text-[#6F6B68]">
                            ${escapeHTML(greetingInfo ? greetingInfo.greetingText : 'Hi there 👋')}
                        </div>
                        <h3 class="font-heading text-xl sm:text-2xl font-bold text-[#202124]">
                            ${window.t ? window.t('modes.urgent.statePlanStale', {}, 'Your plan needs an update.') : 'Your plan needs an update.'}
                        </h3>
                        <p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed">
                            ${window.t ? window.t('modes.urgent.statePlanStaleDesc', {}, 'Some planned work dates have passed while tasks are still unfinished. We don\'t reschedule automatically—let\'s review and adjust your plan calmly together.') : 'Some planned work dates have passed while tasks are still unfinished. We don\'t reschedule automatically—let\'s review and adjust your plan calmly together.'}
                        </p>
                    </div>
                </div>

                <div class="relative z-10 p-3.5 bg-white/90 rounded-2xl border border-[#FFD2BA] text-xs text-amber-950 space-y-1.5">
                    <div class="font-bold text-stone-700 uppercase text-[10px] tracking-wider">Unfinished from past dates:</div>
                    ${staleTasks.map(t => `
                        <div class="flex items-center justify-between">
                            <span class="font-semibold">• ${escapeHTML(t.task.name)}</span>
                            <span class="text-stone-500 text-[11px]">Was scheduled: ${escapeHTML(t.dayLabel || t.dayDate)}</span>
                        </div>
                    `).join('')}
                </div>

                <div class="relative z-10 pt-1 flex flex-wrap items-center gap-3">
                    <button onclick="window.TempoApp.navigateTo('plan-workspace');"
                            class="btn-primary px-5 py-2.5 rounded-xl font-bold text-xs shadow-sm transition cursor-pointer">
                        ${window.t ? window.t('modes.urgent.updateSchedule', {}, 'Review & update plan →') : 'Review & update plan →'}
                    </button>
                    <button onclick="window.TempoMode.dismissStaleWarning()" 
                            class="px-4 py-2.5 rounded-xl border border-[#FFD2BA] text-xs font-semibold text-[#B83D08] bg-white hover:bg-[#FFE9DC]/50 transition cursor-pointer">
                        Dismiss for now
                    </button>
                </div>
            </div>
        `;
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
            <div class="bg-gradient-to-br from-[#FFF9F5] via-[#FFF3EB] to-[#FFEFE6] border-2 border-[#FFD2BA] rounded-3xl p-5 sm:p-6 space-y-4 shadow-sm relative overflow-hidden">
                <div class="absolute -right-8 -top-8 w-32 h-32 bg-[#FF6B2C]/5 rounded-full blur-2xl pointer-events-none"></div>
                <div class="relative z-10 flex items-start space-x-3.5">
                    <span class="text-2xl mt-0.5">⏰</span>
                    <div class="space-y-1">
                        <span class="text-[11px] font-bold uppercase tracking-wider text-[#B83D08]">PLANNED WINDOW ENDED</span>
                        <div class="text-xs sm:text-sm font-semibold text-[#6F6B68]">
                            ${escapeHTML(greetingInfo ? greetingInfo.greetingText : 'Hi there 👋')}
                        </div>
                        <h3 class="font-heading text-xl sm:text-2xl font-bold text-[#202124]">
                            ${window.t ? window.t('modes.urgent.stateTimeEnded', {}, 'Your planned work time for today has ended.') : 'Your planned work time for today has ended.'}
                        </h3>
                        <p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed">
                            <strong class="text-[#202124]">${escapeHTML(taskName)}</strong> is still in progress.
                        </p>
                    </div>
                </div>

                ${hasDeadlineRisk ? `
                    <div class="relative z-10 p-3 bg-rose-50 border border-rose-200 rounded-2xl text-xs text-rose-900 space-y-1">
                        <div class="font-bold flex items-center space-x-1">
                            <span>⚠️</span>
                            <span>Upcoming Deadline Notice:</span>
                        </div>
                        <p>This task is due tonight or early tomorrow. If you choose to stop now, you may want to open your plan and allocate a morning block tomorrow.</p>
                    </div>
                ` : ''}

                <div class="relative z-10 space-y-2 pt-1">
                    <span class="text-xs font-bold text-[#202124]">What would you like to do?</span>
                    <div class="flex flex-wrap items-center gap-3">
                        <button onclick="window.TempoMode.stopForToday()" 
                                class="px-4 py-2.5 rounded-xl bg-white border border-[#FFD2BA] hover:bg-stone-50 text-stone-800 text-xs font-bold transition cursor-pointer">
                            Stop for today
                        </button>
                        <button onclick="window.TempoMode.keepWorkingToday()" 
                                class="btn-primary px-5 py-2.5 rounded-xl text-xs font-bold shadow-sm transition cursor-pointer">
                            Keep working
                        </button>
                        <button onclick="window.TempoApp.navigateTo('plan-workspace');" 
                                class="px-4 py-2.5 rounded-xl border border-[#EAE4DF] text-xs font-semibold text-gray-700 bg-white hover:bg-stone-50 transition cursor-pointer">
                            Adjust my plan
                        </button>
                    </div>
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

        const nextItem = futureTasks[0];
        const nextScheduleText = nextItem
            ? `${nextItem.dayLabel || nextItem.dayDate}${nextItem.startTime ? ` · ${nextItem.startTime}` : ''}`
            : 'No further dates scheduled';

        return `
            <div class="bg-gradient-to-br from-[#FFF9F5] via-[#FFF3EB] to-[#FFEFE6] border-2 border-[#FFD2BA] rounded-3xl p-5 sm:p-6 space-y-4 shadow-sm relative overflow-hidden">
                <div class="absolute -right-8 -top-8 w-32 h-32 bg-[#FF6B2C]/5 rounded-full blur-2xl pointer-events-none"></div>
                <div class="relative z-10 flex items-center space-x-2">
                    <span class="w-6 h-6 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold text-xs">✓</span>
                    <span class="text-[11px] font-extrabold uppercase tracking-wider text-emerald-800">${window.t ? window.t('modes.urgent.todaysWorkDone', {}, "TODAY'S WORK DONE") : "TODAY'S WORK DONE"}</span>
                </div>

                <div class="relative z-10 space-y-1">
                    <div class="text-xs sm:text-sm font-semibold text-[#6F6B68]">
                        ${escapeHTML(greetingInfo ? greetingInfo.greetingText : 'Hi there 👋')}
                    </div>
                    <h3 class="font-heading text-xl sm:text-2xl font-extrabold text-[#202124]">
                        ${window.t ? window.t('modes.urgent.stateTodayComplete', {}, "You're done for today.") : "You're done for today."}
                    </h3>
                    <p class="text-xs sm:text-sm text-[#6F6B68]">
                        ${window.t ? window.t('modes.urgent.stateTodayCompleteDesc', {}, 'You\'ve completed what you planned for today. Protect your rest.') : 'You\'ve completed what you planned for today. Protect your rest.'}
                    </p>
                </div>

                <div class="relative z-10 p-3.5 bg-white/90 border border-[#FFD2BA] rounded-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
                    <div class="space-y-0.5">
                        <span class="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Next planned work:</span>
                        <div class="font-bold text-sm text-[#202124]">${escapeHTML(nextScheduleText)}</div>
                        ${nextItem ? `<p class="text-[#6F6B68] text-[11px]">${escapeHTML(nextItem.task.name)}</p>` : ''}
                    </div>
                    ${nextItem ? `
                        <button onclick="window.TempoApp.navigateTo('plan-workspace');"
                                class="px-4 py-2 rounded-xl border border-[#FFD2BA] bg-white font-semibold text-xs text-gray-700 hover:bg-stone-50 transition self-start sm:self-auto cursor-pointer">
                            View tomorrow →
                        </button>
                    ` : ''}
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
            <div class="bg-gradient-to-br from-[#FFF9F5] via-[#FFF3EB] to-[#FFEFE6] border-2 border-[#FFD2BA] rounded-3xl p-5 sm:p-6 space-y-3.5 shadow-sm relative overflow-hidden">
                <div class="absolute -right-8 -top-8 w-32 h-32 bg-[#FF6B2C]/5 rounded-full blur-2xl pointer-events-none"></div>
                <div class="relative z-10 space-y-1">
                    <span class="text-[11px] font-extrabold uppercase tracking-wider text-[#6F6B68]">SCHEDULE OVERVIEW</span>
                    <div class="text-xs sm:text-sm font-semibold text-[#6F6B68]">
                        ${escapeHTML(greetingInfo ? greetingInfo.greetingText : 'Hi there 👋')}
                    </div>
                    <h3 class="font-heading text-xl sm:text-2xl font-bold text-[#202124]">
                        ${window.t ? window.t('modes.urgent.stateNoWork', {}, 'Nothing planned for today.') : 'Nothing planned for today.'}
                    </h3>
                    <p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed">
                        ${window.t ? window.t('modes.urgent.stateNoWorkDesc', {}, 'Your Urgent Plan continues on a future date.') : 'Your Urgent Plan continues on'} <strong>${escapeHTML(nextDateLabel)}</strong>.
                    </p>
                </div>

                <div class="relative z-10 pt-1 flex items-center space-x-3">
                    <button onclick="window.TempoApp.navigateTo('plan-workspace');"
                            class="px-4 py-2.5 rounded-xl border border-[#FFD2BA] text-xs font-semibold text-gray-700 bg-white hover:bg-stone-50 transition cursor-pointer">
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
        let nowItem = todayTasks.find(pt => pt.task.isInProgress && !pt.task.completed);
        if (!nowItem) {
            nowItem = todayTasks.find(pt => !pt.task.completed);
        }
        if (!nowItem) {
            nowItem = todayTasks[0];
        }

        const completedTodayCount = todayTasks.filter(pt => pt.task.completed).length;
        const completionPercent = todayTasks.length > 0 ? Math.round((completedTodayCount / todayTasks.length) * 100) : 0;

        // Subtask / next concrete action logic
        let nextActionText = "Begin focused preliminary work block.";
        let actionStepsLabel = "1 action step";
        if (nowItem && nowItem.task.subtasks && nowItem.task.subtasks.length > 0) {
            const incompleteSubtasks = nowItem.task.subtasks.filter(s => !s.completed);
            const completedSubtasksCount = nowItem.task.subtasks.filter(s => s.completed).length;
            const totalSubtasksCount = nowItem.task.subtasks.length;
            nextActionText = incompleteSubtasks.length > 0 ? incompleteSubtasks[0].title : (nowItem.task.description || "All preliminary steps completed.");
            actionStepsLabel = `${completedSubtasksCount} / ${totalSubtasksCount} action steps`;
        } else if (nowItem && nowItem.task.description) {
            nextActionText = nowItem.task.description;
        }

        const deadlineText = nowItem && nowItem.task.hasDeadline
            ? `${window.t ? window.t('modes.urgent.due', {}, 'Due') : 'Due'} ${window.TempoI18n ? window.TempoI18n.formatDeadline(nowItem.task.deadlineDate, nowItem.task.deadlineTime) : formatHumanDeadline(nowItem.task.deadlineDate, nowItem.task.deadlineTime)}`
            : (window.t ? window.t('workspace.noDeadline', {}, 'No fixed deadline') : 'No fixed deadline');

        const durationText = nowItem
            ? (nowItem.task.isUnknownDuration ? (window.t ? window.t('common.notEstimated', {}, 'Time not estimated') : 'Time not estimated') : `~ ${nowItem.task.durationLabel || '45 min'}`)
            : "~ 45 min";

        // Check for "Needs Attention" items (ONLY if actual issues exist!)
        const needsAttentionItems = checkNeedsAttentionIssues(confirmedPlan, todayStr);

        return `
            <!-- Priority #1: YOUR TASK FOR NOW -->
            ${nowItem ? `
                <div class="urgent-card-now bg-gradient-to-br from-[#FFF9F5] via-[#FFF3EB] to-[#FFEFE6] border-2 border-[#FFD2BA] rounded-3xl p-6 sm:p-8 space-y-4 shadow-sm relative overflow-hidden" data-tempo-ui="urgent-task-now">
                    <div class="absolute -right-8 -top-8 w-32 h-32 bg-[#FF6B2C]/5 rounded-full blur-2xl pointer-events-none"></div>
                    <div class="absolute -left-8 -bottom-8 w-32 h-32 bg-[#FF6B2C]/5 rounded-full blur-2xl pointer-events-none"></div>

                    <!-- Badge Row: YOUR TASK FOR NOW & NOW -->
                    <div class="relative z-10 flex items-center justify-between">
                        <div class="flex items-center space-x-2">
                            <span class="w-2.5 h-2.5 rounded-full bg-[#FF6B2C] animate-pulse inline-block"></span>
                            <span class="text-[11px] font-extrabold uppercase tracking-wider text-[#B83D08]">
                                ${window.t ? window.t('modes.urgent.taskForNow', {}, 'YOUR TASK FOR NOW') : 'YOUR TASK FOR NOW'}
                            </span>
                        </div>
                        <span class="px-3 py-1 rounded-full text-[10px] font-extrabold bg-[#FF6B2C] text-white tracking-wider shadow-xs">
                            ${window.t ? window.t('common.now', {}, 'NOW') : 'NOW'}
                        </span>
                    </div>

                    <!-- Greeting & Task Title Block -->
                    <div class="relative z-10 space-y-1.5">
                        <div class="text-xs sm:text-sm font-semibold text-[#6F6B68]">
                            ${escapeHTML(greetingInfo ? greetingInfo.greetingText : 'Hi there 👋')}
                        </div>
                        <h3 class="font-heading text-2xl sm:text-3xl font-extrabold text-[#202124] tracking-tight">
                            ${escapeHTML(nowItem.task.name)}
                        </h3>
                        <p class="text-sm sm:text-base font-semibold text-[#6F6B68]">
                            ${escapeHTML(nextActionText)}
                        </p>
                    </div>

                    <!-- Metadata Row -->
                    <div class="relative z-10 flex flex-wrap items-center gap-3 sm:gap-4 text-xs font-medium text-[#6F6B68] pt-1">
                        <div class="flex items-center space-x-1.5">
                            <svg class="w-4 h-4 text-[#B83D08] shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>
                            </svg>
                            <span>${escapeHTML(deadlineText)}</span>
                        </div>
                        <span class="text-[#FFD2BA] hidden sm:inline">|</span>
                        <div class="flex items-center space-x-1.5">
                            <svg class="w-4 h-4 text-[#B83D08] shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                            </svg>
                            <span>${escapeHTML(durationText)}</span>
                        </div>
                        <span class="text-[#FFD2BA] hidden sm:inline">|</span>
                        <div class="flex items-center space-x-1.5">
                            <svg class="w-4 h-4 text-[#B83D08] shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"/>
                            </svg>
                            <span>${escapeHTML(actionStepsLabel)}</span>
                        </div>
                    </div>

                    <!-- Action Buttons Row -->
                    <div class="relative z-10 pt-3 flex flex-wrap items-center gap-3">
                        <button onclick="window.TempoMode.startTaskFocus('${nowItem.task.id}')"
                                class="btn-primary px-5 py-2.5 rounded-xl font-bold text-xs sm:text-sm shadow-md inline-flex items-center space-x-2 transition cursor-pointer">
                            <span class="text-xs">▶</span>
                            <span>${window.t ? window.t('modes.urgent.focusOnTask', {}, 'Focus on this task →') : 'Focus on this task →'}</span>
                        </button>
                        <button onclick="window.TempoApp.navigateTo('plan-workspace'); if (window.TempoPlanWorkspace && window.TempoPlanWorkspace.selectTask) { window.TempoPlanWorkspace.selectTask('${nowItem.task.id}'); }"
                                class="px-4 py-2.5 rounded-xl border border-[#EAE4DF] text-xs font-bold text-[#202124] bg-white hover:bg-stone-50 transition shadow-xs cursor-pointer inline-flex items-center space-x-1.5">
                            <span>${window.t ? window.t('modes.urgent.viewTask', {}, 'View task →') : 'View task →'}</span>
                        </button>
                    </div>
                </div>
            ` : ''}

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

        if (state === 'PLAN_INCOMPLETE' || !confirmedPlan || !confirmedPlan.plannedTasks || confirmedPlan.plannedTasks.length === 0) {
            return `
                <div class="space-y-4">
                    <div class="flex items-center justify-between pb-1">
                        <h3 class="font-heading text-lg sm:text-xl font-extrabold text-[#202124]">
                            ${window.t ? window.t('modes.urgent.planForToday', {}, 'Your plan for today') : 'Your plan for today'}
                        </h3>
                        <button onclick="window.TempoApp.navigateTo('emergency'); if (window.TempoEmergencyFlow && window.TempoEmergencyFlow.goToStage) { window.TempoEmergencyFlow.goToStage('${currentStage || 'entry'}'); }"
                                class="text-xs font-bold text-[#FF6B2C] hover:text-[#B83D08] flex items-center space-x-1 transition cursor-pointer">
                            <span>Resume Setup</span>
                            <span>→</span>
                        </button>
                    </div>
                    <div class="p-4 bg-stone-50 border border-stone-200/60 rounded-2xl text-xs text-[#6F6B68] space-y-2">
                        <div class="font-bold text-[#202124]">Plan setup in progress</div>
                        <p>Your task schedule and timeline will appear here once you finalize your urgent plan.</p>
                    </div>
                </div>
                <div class="pt-4 border-t border-stone-100 flex items-center justify-between text-xs text-[#8C8782]">
                    <span>Step: <strong>${escapeHTML(currentStage || 'entry')}</strong></span>
                    <button onclick="window.TempoMode.openChangeModeModal()" class="hover:text-[#202124] underline cursor-pointer">
                        ${window.t ? window.t('modes.selector.switchMode', {}, 'Switch mode') : 'Switch mode'}
                    </button>
                </div>
            `;
        }

        const allPlanned = confirmedPlan.plannedTasks || [];
        const todayTasks = allPlanned.filter(pt => pt.dayDate === todayStr);

        if (todayTasks.length === 0) {
            const upcomingTasks = allPlanned.filter(pt => pt.dayDate > todayStr);
            const nextItem = upcomingTasks[0];
            const nextDateLabel = nextItem ? (nextItem.dayLabel || nextItem.dayDate) : 'a future date';

            return `
                <div class="space-y-4">
                    <div class="flex items-center justify-between pb-1">
                        <h3 class="font-heading text-lg sm:text-xl font-extrabold text-[#202124]">
                            ${window.t ? window.t('modes.urgent.planForToday', {}, 'Your plan for today') : 'Your plan for today'}
                        </h3>
                        <button onclick="window.TempoApp.navigateTo('plan-workspace');"
                                class="text-xs font-bold text-[#FF6B2C] hover:text-[#B83D08] flex items-center space-x-1 transition cursor-pointer">
                            <span>${window.t ? window.t('modes.urgent.viewEditPlan', {}, 'View / Edit Plan') : 'View / Edit Plan'}</span>
                            <span>→</span>
                        </button>
                    </div>
                    <div class="p-4 bg-stone-50 border border-stone-200/60 rounded-2xl text-xs text-[#6F6B68] space-y-2">
                        <div class="font-bold text-[#202124]">Nothing scheduled today</div>
                        <p>Your Urgent Plan continues on <strong>${escapeHTML(nextDateLabel)}</strong>.</p>
                    </div>
                </div>
                <div class="pt-4 border-t border-stone-100 flex items-center justify-between text-xs text-[#8C8782]">
                    <span>${upcomingTasks.length} upcoming task${upcomingTasks.length === 1 ? '' : 's'}</span>
                    <button onclick="window.TempoApp.navigateTo('plan-workspace');" class="hover:text-[#202124] underline cursor-pointer">
                        View Plan Schedule →
                    </button>
                </div>
            `;
        }

        // We have tasks for today!
        let nowItem = todayTasks.find(pt => pt.task.isInProgress && !pt.task.completed);
        if (!nowItem) {
            nowItem = todayTasks.find(pt => !pt.task.completed);
        }
        if (!nowItem) {
            nowItem = todayTasks[0];
        }

        const completedTodayCount = todayTasks.filter(pt => pt.task.completed).length;
        const completionPercent = todayTasks.length > 0 ? Math.round((completedTodayCount / todayTasks.length) * 100) : 0;

        return `
            <div class="space-y-4">
                <!-- Header -->
                <div class="flex items-center justify-between pb-1">
                    <h3 class="font-heading text-lg sm:text-xl font-extrabold text-[#202124]">
                        ${window.t ? window.t('modes.urgent.planForToday', {}, 'Your plan for today') : 'Your plan for today'}
                    </h3>
                    <button onclick="window.TempoApp.navigateTo('plan-workspace');"
                            class="text-xs font-bold text-[#FF6B2C] hover:text-[#B83D08] flex items-center space-x-1 transition cursor-pointer">
                        <span>${window.t ? window.t('modes.urgent.viewEditPlan', {}, 'View / Edit Plan') : 'View / Edit Plan'}</span>
                        <span>→</span>
                    </button>
                </div>

                <!-- Progress Header & Bar -->
                <div class="space-y-1.5">
                    <div class="flex items-center justify-between text-xs">
                        <span class="text-[#6F6B68] font-medium">${window.t ? window.t('modes.urgent.completedOf', { completed: completedTodayCount, total: todayTasks.length }, `${completedTodayCount} of ${todayTasks.length} completed`) : `${completedTodayCount} of ${todayTasks.length} completed`}</span>
                        <span class="font-bold text-[#202124]">${completionPercent}%</span>
                    </div>
                    <div class="w-full bg-stone-100 rounded-full h-2 overflow-hidden">
                        <div class="bg-[#FF6B2C] h-2 rounded-full transition-all duration-300" style="width: ${completionPercent}%"></div>
                    </div>
                </div>

                <!-- Timeline Task List -->
                <div class="pt-2 space-y-4">
                    ${todayTasks.map((item, idx) => {
                        const isDone = item.task.completed === true;
                        const isNow = !isDone && nowItem && item.task.id === nowItem.task.id;
                        const isLast = idx === todayTasks.length - 1;

                        let bulletHTML = '';
                        if (isDone) {
                            bulletHTML = `
                                <div class="w-6 h-6 rounded-full bg-emerald-600 text-white flex items-center justify-center text-xs font-bold shrink-0 z-10 shadow-xs">
                                    ✓
                                </div>
                            `;
                        } else if (isNow) {
                            bulletHTML = `
                                <div class="w-6 h-6 rounded-full bg-[#FF6B2C] border-2 border-white shadow-xs flex items-center justify-center shrink-0 z-10">
                                    <div class="w-2 h-2 rounded-full bg-white"></div>
                                </div>
                            `;
                        } else {
                            bulletHTML = `
                                <div class="w-6 h-6 rounded-full border-2 border-stone-300 bg-white flex items-center justify-center shrink-0 z-10"></div>
                            `;
                        }

                        let badgeHTML = '';
                        if (isDone) {
                            badgeHTML = `<span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">${window.t ? window.t('modes.urgent.completedBadge', {}, 'Completed') : 'Completed'}</span>`;
                        } else if (isNow) {
                            badgeHTML = `<span class="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold bg-[#FFE9DC] text-[#B83D08]">${window.t ? window.t('common.now', {}, 'NOW') : 'NOW'}</span>`;
                        } else {
                            badgeHTML = `<span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-stone-100 text-stone-600">${window.t ? window.t('common.upNext', {}, 'UP NEXT') : 'UP NEXT'}</span>`;
                        }

                        const timeDurationStr = `${item.startTime || ''}${item.startTime ? ' · ' : ''}~${item.task.isUnknownDuration ? (window.t ? window.t('common.notEstimated', {}, 'Not estimated') : 'Not estimated') : (item.task.durationLabel || '45 min')}`;

                        return `
                            <div class="urgent-timeline-item flex items-start space-x-3 group relative">
                                ${!isLast ? '<div class="urgent-timeline-line"></div>' : ''}
                                
                                <!-- Bullet -->
                                <div class="pt-0.5">
                                    ${bulletHTML}
                                </div>

                                <!-- Content -->
                                <div class="flex-1 min-w-0">
                                    <div class="flex items-start justify-between gap-2">
                                        <div class="min-w-0 flex-1">
                                            <h4 class="text-xs font-bold truncate ${isDone ? 'line-through text-stone-400' : 'text-[#202124]'}">
                                                ${escapeHTML(item.task.name)}
                                            </h4>
                                            <p class="text-[11px] text-[#6F6B68]">
                                                ${escapeHTML(timeDurationStr)}
                                            </p>
                                        </div>
                                        <div class="flex items-center space-x-1.5 shrink-0">
                                            ${badgeHTML}
                                            <button type="button" onclick="window.TempoMode.toggleTaskCompletion('${item.task.id}')"
                                                    title="${isDone ? 'Mark as incomplete' : 'Mark as completed'}"
                                                    class="p-1 rounded-lg text-stone-400 hover:text-stone-700 hover:bg-stone-100 transition text-xs cursor-pointer">
                                                •••
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        `;
                    }).join('')}
                </div>
            </div>
        `;
    }

    // -------------------------------------------------------------------------
    // SHARED ECOSYSTEM FOR URGENT MODE (Excluded in favor of dedicated Urgent Support Row)
    // -------------------------------------------------------------------------
    function renderEmodeSharedEcosystem() {
        return '';
    }

    // -------------------------------------------------------------------------
    // DEDICATED URGENT SUPPORT ROW (Feeling overwhelmed? + Focus now)
    // -------------------------------------------------------------------------
    function renderSupportRowHTML() {
        return `
            <div class="urgent-support-row" data-tempo-ui="urgent-support">
                <!-- Card 1: Feeling overwhelmed? -->
                <div class="urgent-card-overwhelmed bg-gradient-to-br from-[#FFF9F5] via-[#FFF3EB] to-[#FFEFE6] border border-[#FFD2BA] rounded-3xl p-5 sm:p-6 space-y-3.5 shadow-xs">
                    <div class="flex items-center space-x-3">
                        <div class="w-9 h-9 rounded-2xl bg-[#FFE9DC] text-[#FF6B2C] flex items-center justify-center text-lg shrink-0">
                            ⚡
                        </div>
                        <div>
                            <h4 class="font-heading text-base sm:text-lg font-bold text-[#202124]">
                                ${window.t ? window.t('modes.urgent.overwhelmed', {}, 'Feeling overwhelmed?') : 'Feeling overwhelmed?'}
                            </h4>
                            <p class="text-xs text-[#6F6B68] leading-relaxed">
                                ${window.t ? window.t('modes.urgent.overwhelmedDesc', {}, 'Take a few minutes to calm things down and clear your head.') : 'Take a few minutes to calm things down and clear your head.'}
                            </p>
                        </div>
                    </div>
                    <div class="pt-1 flex flex-wrap items-center gap-2.5">
                        <button type="button"
                                onclick="if (window.TempoStressRelief && window.TempoStressRelief.openModal) { window.TempoStressRelief.openModal(); } else if (window.TempoTriage && window.TempoTriage.openQuickReliefModal) { window.TempoTriage.openQuickReliefModal(); }"
                                class="btn-primary px-4 py-2 rounded-xl font-bold text-xs shadow-xs inline-flex items-center space-x-1.5 transition cursor-pointer">
                            <span>${window.t ? window.t('modes.urgent.quickStressRelief', {}, 'Quick Stress Relief') : 'Quick Stress Relief'}</span>
                            <span>→</span>
                        </button>
                        <button type="button"
                                onclick="if (window.TempoTriage && window.TempoTriage.openBoxBreathingModal) { window.TempoTriage.openBoxBreathingModal(); } else if (window.TempoBreathing && window.TempoBreathing.openModal) { window.TempoBreathing.openModal(); }"
                                class="px-3.5 py-2 rounded-xl border border-[#FFD2BA] bg-white text-xs font-bold text-[#B83D08] hover:bg-[#FFF9F5] transition shadow-xs inline-flex items-center space-x-1.5 cursor-pointer">
                            <span>💨</span>
                            <span>${window.t ? window.t('modes.urgent.breathing', {}, 'Breathing') : 'Breathing'}</span>
                        </button>
                    </div>
                </div>

                <!-- Card 2: Focus now -->
                <div class="urgent-card-focus-now bg-[#FFFDFB] border border-[#EAE4DF] rounded-3xl p-5 sm:p-6 space-y-3.5 shadow-xs flex flex-col justify-between">
                    <div class="flex items-center space-x-3">
                        <div class="w-9 h-9 rounded-2xl bg-orange-50 text-[#FF6B2C] flex items-center justify-center text-lg shrink-0">
                            🎯
                        </div>
                        <div>
                            <h4 class="font-heading text-base sm:text-lg font-bold text-[#202124]">
                                ${window.t ? window.t('modes.urgent.focusNow', {}, 'Focus now') : 'Focus now'}
                            </h4>
                            <p class="text-xs text-[#6F6B68] leading-relaxed">
                                ${window.t ? window.t('modes.urgent.focusNowDesc', {}, 'Start a Focus session at your own pace.') : 'Start a Focus session at your own pace.'}
                            </p>
                        </div>
                    </div>
                    <div class="pt-1">
                        <button type="button"
                                onclick="if (window.TempoFocusZone && window.TempoFocusZone.openQuickEntry) { window.TempoFocusZone.openQuickEntry(); } else if (window.TempoTriage && window.TempoTriage.launchFocusMode) { window.TempoTriage.launchFocusMode(); }"
                                class="px-4 py-2 rounded-xl bg-[#FFE9DC] hover:bg-[#FFDFC9] text-[#B83D08] font-bold text-xs border border-[#FFD2BA] transition shadow-xs inline-flex items-center space-x-1.5 cursor-pointer">
                            <span>${window.t ? window.t('modes.urgent.startFocus', {}, 'Start Focus →') : 'Start Focus →'}</span>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    // -------------------------------------------------------------------------
    // -------------------------------------------------------------------------
    // TEMPO POSTS COMPONENT (Lightweight Community Social Feed Previews)
    // -------------------------------------------------------------------------
    function renderTempoPostsSection() {
        const posts = (window.TempoCommunity && window.TempoCommunity.getAllPosts)
            ? window.TempoCommunity.getAllPosts().slice(0, 2)
            : [];

        const postsCardsHTML = (posts.length > 0 && window.TempoCommunity && window.TempoCommunity.renderPostCardHTML)
            ? posts.map(p => window.TempoCommunity.renderPostCardHTML(p)).join('')
            : '';

        return `
            <div class="urgent-section-posts space-y-4 pt-2" data-tempo-ui="urgent-posts">
                <!-- Header -->
                <div class="flex items-center justify-between">
                    <div class="space-y-0.5">
                        <div class="flex items-center space-x-2">
                            <h3 class="font-heading text-lg sm:text-xl font-extrabold text-[#202124]">
                                ${window.t ? window.t('posts.title', {}, 'Tempo Posts') : 'Tempo Posts'}
                            </h3>
                            <span class="text-xs text-[#6F6B68] font-medium hidden sm:inline">• A little something for when you have space.</span>
                        </div>
                        <p class="text-xs text-[#6F6B68] sm:hidden">A little something for when you have space.</p>
                    </div>
                    <button type="button" 
                            onclick="if (window.TempoCommunity) { window.TempoCommunity.openCommunityModal(); }" 
                            class="text-xs font-bold text-[#FF6B2C] hover:text-[#B83D08] flex items-center space-x-1 transition cursor-pointer">
                        <span>${window.t ? window.t('posts.seeAllPosts', {}, 'See all posts →') : 'See all posts →'}</span>
                    </button>
                </div>

                <!-- Social Post Previews: 1-2 posts side by side on desktop, stacked on mobile -->
                <div id="urgent-community-posts-list" class="grid grid-cols-1 md:grid-cols-2 gap-4">
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
        if (currentMode === MODES.RECOVERY) renderRmodeHome();
    }

    function handleSelfCheckSetupClick() {
        if (window.TempoRecoverySetup && typeof window.TempoRecoverySetup.open === 'function') {
            window.TempoRecoverySetup.open(1);
        } else if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.openSetup === 'function') {
            window.TempoRecoverySelfCheck.openSetup();
        } else if (window.TempoApp) {
            window.TempoApp.showToast("Custom Self-check setup will be available.");
        }
    }

    function handleSelfCheckAction(action) {
        if (action === 'history') {
            if (window.TempoSelfCheckHistory && typeof window.TempoSelfCheckHistory.open === 'function') {
                window.TempoSelfCheckHistory.open();
                return;
            }
        }
        if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.handleAction === 'function') {
            window.TempoRecoverySelfCheck.handleAction(action);
        } else if (window.TempoApp) {
            if (action === 'checkin') {
                window.TempoApp.showToast("Daily check-in form will be available in Phase 2.");
            } else if (action === 'manage') {
                window.TempoApp.showToast("Tracker management will be available in Phase 2.");
            } else if (action === 'view' || action === 'edit') {
                window.TempoApp.showToast("Check-in details will be available in Phase 2.");
            }
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
        if (currentMode === MODES.RECOVERY) renderRmodeHome();
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
        if (currentMode === MODES.RECOVERY) renderRmodeHome();
    }

    function dismissWeeklyReviewNotice() {
        weeklyReviewDismissed = true;
        if (window.TempoWeeklyReview && typeof window.TempoWeeklyReview.getLatestEligibleWeek === 'function') {
            const wk = window.TempoWeeklyReview.getLatestEligibleWeek();
            if (wk) window.TempoWeeklyReview.snoozeOrDismissNotice(wk.start);
        }
        if (currentMode === MODES.RECOVERY) renderRmodeHome();
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

    function renderRmodeHome() {
        applyModeVisibility(MODES.RECOVERY);

        const rmodeBox = document.getElementById('rmode-home-content');
        if (!rmodeBox) return;

        // Shared emergency state: Prefer active plan from TempoPlanStore, fallback to TempoEmergencyFlow
        const activeStorePlan = window.TempoPlanStore && window.TempoPlanStore.getActivePlan
            ? window.TempoPlanStore.getActivePlan('emergency')
            : null;
        const confirmedPlan = (activeStorePlan && activeStorePlan.plannedTasks && activeStorePlan.plannedTasks.length > 0)
            ? activeStorePlan
            : ((window.TempoEmergencyFlow && window.TempoEmergencyFlow.getConfirmedPlan) ? window.TempoEmergencyFlow.getConfirmedPlan() : null);

        const todayStr = getTodayISOString();
        const profile = window.TempoAuth ? window.TempoAuth.getCurrentProfile() : null;
        const greetingInfo = getSafeGreetingInfo(profile);
        const selfCheckState = getSelfCheckState();
        const recentlyState = getRecentlyState();
        const isWeeklyReviewReady = checkIsWeeklyReviewReady();
        const latestEligibleWeek = (window.TempoWeeklyReview && typeof window.TempoWeeklyReview.getLatestEligibleWeek === 'function')
            ? window.TempoWeeklyReview.getLatestEligibleWeek()
            : null;

        rmodeBox.innerHTML = `
            ${renderRmodeHeader()}
            ${renderRecoveryIntroBanner()}
            <div class="space-y-8" data-tempo-ui="recovery-home-shell">
                <!-- Main Asymmetric Grid: ~65% Left / ~35% Right on Desktop -->
                <div class="recovery-home-main-grid">
                    <!-- LEFT COLUMN (~65%) -->
                    <div class="recovery-left-col">
                        ${renderSelfCheckCard(selfCheckState, greetingInfo)}
                    </div>

                    <!-- RIGHT COLUMN (~35%) -->
                    <div class="recovery-right-col space-y-6">
                        ${renderRecoveryNoteCard()}
                        ${renderRecentlyCard(recentlyState)}
                    </div>
                </div>

                ${renderWeeklyReviewShell(isWeeklyReviewReady, latestEligibleWeek)}
                ${renderRecoveryTodaySection(confirmedPlan, todayStr)}
                ${renderRecoverySharedEcosystem()}
                ${renderRecoveryPostsSection()}
            </div>
        `;

        // Also trigger community posts preview sync
        if (window.TempoCommunity && typeof window.TempoCommunity.renderRecoveryPreview === 'function') {
            window.TempoCommunity.renderRecoveryPreview();
        }
    }

    function renderUmodeHome() {
        applyModeVisibility(MODES.UNCLEAR);

        if (window.TempoUnclearMode && typeof window.TempoUnclearMode.renderHome === 'function') {
            window.TempoUnclearMode.renderHome();
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
    }

    function renderActiveModeHome() {
        renderShellIndicator();
        switch (currentMode) {
            case MODES.EMERGENCY:
                renderEmodeHome();
                break;
            case MODES.RECOVERY:
                renderRmodeHome();
                break;
            case MODES.UNCLEAR:
                renderUmodeHome();
                break;
            case MODES.DEFAULT:
            default:
                restoreDefaultHome();
                break;
        }
    }

    function renderRmodeHeader() {
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

        return `
            <div class="relative pb-1">
                <!-- Top Mode Selector & Date Row -->
                <div class="flex items-center justify-between gap-4">
                    <!-- Anchored Mode Selector Dropdown -->
                    <div id="home-mode-selector-wrapper" class="relative inline-block text-left">
                        <button id="btn-home-mode-selector" 
                                type="button" 
                                data-tempo-ui="mode-selector-btn"
                                onclick="window.TempoMode.toggleModeDropdown(event)" 
                                class="px-3.5 py-1.5 rounded-full text-xs font-bold bg-[#EDF7F1] text-[#166545] hover:bg-[#DDF0E5] border border-[#CDE9DA] transition flex items-center space-x-1.5 shadow-xs cursor-pointer"
                                aria-haspopup="true"
                                aria-expanded="false"
                                title="Switch Tempo Mode">
                            <span>🌱</span>
                            <span class="font-extrabold">${window.t ? window.t('modes.recovery.name', {}, 'Recovery Mode') : 'Recovery Mode'}</span>
                            <span class="text-[10px] ml-0.5 opacity-80">▾</span>
                        </button>
                        <div id="home-mode-selector-dropdown" class="hidden absolute left-0 mt-2 w-72 sm:w-80 bg-white rounded-2xl shadow-xl border border-[#EAE4DF] z-50 overflow-hidden" role="menu"></div>
                    </div>

                    <!-- Date Display -->
                    <div class="hidden sm:block text-xs font-semibold text-[#6F6B68]">
                        ${escapeHTML(formattedDate)}
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

    function renderSelfCheckCard(selfCheckState, greetingInfo) {
        const greetingText = greetingInfo ? greetingInfo.greetingText : 'Hi there 👋';

        if (selfCheckState && selfCheckState.type === 'STATE_B') {
            const streakCount = selfCheckState.streak || 0;
            const trackerCount = selfCheckState.trackersCount || 0;
            const days = selfCheckState.days || ['M', 'T', 'W', 'T', 'F', 'S', 'S'];
            const dayStatus = selfCheckState.dayStatus || ['done', 'done', 'done', 'done', 'done', 'done', 'pending'];

            return `
                <div class="recovery-card-selfcheck bg-white border border-[#CDE9DA] rounded-3xl p-6 sm:p-8 space-y-5 shadow-xs relative overflow-hidden" data-tempo-ui="recovery-self-check">
                    <div class="text-xs sm:text-sm font-semibold text-[#6F6B68]">
                        ${escapeHTML(greetingText)}
                    </div>
                    <div class="flex items-center space-x-2">
                        <span class="w-2.5 h-2.5 rounded-full bg-[#166545] inline-block"></span>
                        <span class="text-[11px] font-extrabold uppercase tracking-wider text-[#166545]">
                            ${window.t ? window.t('modes.recovery.selfCheck', {}, 'SELF-CHECK') : 'SELF-CHECK'}
                        </span>
                    </div>
                    <div class="space-y-1">
                        <h3 class="font-heading text-xl sm:text-2xl font-extrabold text-[#202124]">
                            How have things been today?
                        </h3>
                        <p class="text-xs text-[#6F6B68] font-medium">${window.t ? window.t('modes.recovery.streakCount', { count: streakCount }, `${streakCount}-day streak`) : `${streakCount} day check-in streak`}</p>
                    </div>

                    <!-- Streak Calendar Row -->
                    <div class="flex items-center space-x-2 py-1">
                        ${days.map((d, i) => `
                            <div class="flex flex-col items-center space-y-1">
                                <div class="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold ${dayStatus[i] === 'done' ? 'bg-[#EDF7F1] text-[#166545] border border-[#CDE9DA]' : (dayStatus[i] === 'pending' ? 'border-2 border-[#166545] text-[#166545]' : 'border border-stone-200 text-stone-400')}">
                                    ${dayStatus[i] === 'done' ? '✓' : (dayStatus[i] === 'pending' ? '●' : '○')}
                                </div>
                                <span class="text-[10px] text-stone-500 font-semibold">${d}</span>
                            </div>
                        `).join('')}
                    </div>

                    <p class="text-xs text-[#6F6B68]">${trackerCount} things you're keeping track of</p>

                    <div class="pt-2 flex flex-wrap items-center gap-3">
                        <button onclick="window.TempoMode.handleSelfCheckAction('checkin')"
                                class="btn-primary px-5 py-2.5 rounded-xl font-bold text-xs sm:text-sm shadow-xs inline-flex items-center space-x-2 transition cursor-pointer">
                            <span>${window.t ? window.t('modes.recovery.checkInToday', {}, 'Check in') : 'Check in'}</span>
                            <span>→</span>
                        </button>
                        <button onclick="window.TempoMode.handleSelfCheckAction('manage')"
                                class="text-xs font-semibold text-[#166545] hover:text-[#0E4A32] transition cursor-pointer">
                            ${window.t ? window.t('modes.recovery.manageSelfCheck', {}, 'Manage Self-check') : 'Manage Self-check'}
                        </button>
                        <span class="text-stone-300">·</span>
                        <button onclick="window.TempoMode.handleSelfCheckAction('history')"
                                class="text-xs font-semibold text-[#166545] hover:text-[#0E4A32] transition cursor-pointer">
                            ${window.t ? window.t('modes.recovery.viewHistory', {}, 'View history') : 'View history'}
                        </button>
                    </div>
                </div>
            `;
        }

        if (selfCheckState && selfCheckState.type === 'STATE_C') {
            const streakCount = selfCheckState.streak || 0;
            const checkedCount = selfCheckState.checkedCount || 0;
            const totalCount = selfCheckState.totalCount || 0;
            const days = selfCheckState.days || ['M', 'T', 'W', 'T', 'F', 'S', 'S'];
            const dayStatus = selfCheckState.dayStatus || ['done', 'done', 'done', 'done', 'done', 'done', 'done'];

            return `
                <div class="recovery-card-selfcheck bg-white border border-[#CDE9DA] rounded-3xl p-6 sm:p-8 space-y-5 shadow-xs relative overflow-hidden" data-tempo-ui="recovery-self-check">
                    <div class="text-xs sm:text-sm font-semibold text-[#6F6B68]">
                        ${escapeHTML(greetingText)}
                    </div>
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-2">
                            <span class="w-2.5 h-2.5 rounded-full bg-[#166545] inline-block"></span>
                            <span class="text-[11px] font-extrabold uppercase tracking-wider text-[#166545]">
                                ${window.t ? window.t('modes.recovery.selfCheck', {}, 'SELF-CHECK') : 'SELF-CHECK'}
                            </span>
                        </div>
                        <span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#EDF7F1] text-[#166545] border border-[#CDE9DA]">
                            ✓ ${window.t ? window.t('modes.recovery.viewToday', {}, 'Checked in today') : 'Checked in today'}
                        </span>
                    </div>
                    <div class="space-y-1">
                        <h3 class="font-heading text-xl sm:text-2xl font-extrabold text-[#202124]">
                            Checked in for today
                        </h3>
                        <p class="text-xs text-[#6F6B68] font-medium">${window.t ? window.t('modes.recovery.streakCount', { count: streakCount }, `${streakCount}-day streak`) : `${streakCount} day check-in streak`}</p>
                    </div>

                    <!-- Streak Calendar Row -->
                    <div class="flex items-center space-x-2 py-1">
                        ${days.map((d, i) => `
                            <div class="flex flex-col items-center space-y-1">
                                <div class="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold ${dayStatus[i] === 'done' ? 'bg-[#EDF7F1] text-[#166545] border border-[#CDE9DA]' : (dayStatus[i] === 'pending' ? 'border-2 border-[#166545] text-[#166545]' : 'border border-stone-200 text-stone-400')}">
                                    ${dayStatus[i] === 'done' ? '✓' : (dayStatus[i] === 'pending' ? '●' : '○')}
                                </div>
                                <span class="text-[10px] text-stone-500 font-semibold">${d}</span>
                            </div>
                        `).join('')}
                    </div>

                    <p class="text-xs text-[#6F6B68]">You checked in on ${checkedCount} of ${totalCount} things.</p>
                    <div class="pt-2 flex flex-wrap items-center gap-3">
                        <button onclick="window.TempoMode.handleSelfCheckAction('view')"
                                class="px-5 py-2.5 rounded-xl font-bold text-xs sm:text-sm bg-[#166545] hover:bg-[#115237] text-white shadow-xs inline-flex items-center space-x-2 transition cursor-pointer">
                            <span>${window.t ? window.t('modes.recovery.viewToday', {}, "View today's check-in") : "View today's check-in"}</span>
                            <span>→</span>
                        </button>
                        <div class="flex items-center space-x-2 text-xs font-semibold text-[#166545]">
                            <button onclick="window.TempoMode.handleSelfCheckAction('edit')" class="hover:text-[#0E4A32] transition cursor-pointer">Edit check-in</button>
                            <span class="text-stone-300">·</span>
                            <button onclick="window.TempoMode.handleSelfCheckAction('manage')" class="hover:text-[#0E4A32] transition cursor-pointer">${window.t ? window.t('modes.recovery.manageSelfCheck', {}, 'Manage Self-check') : 'Manage Self-check'}</button>
                            <span class="text-stone-300">·</span>
                            <button onclick="window.TempoMode.handleSelfCheckAction('history')" class="hover:text-[#0E4A32] transition cursor-pointer">${window.t ? window.t('modes.recovery.viewHistory', {}, 'History') : 'History'}</button>
                        </div>
                    </div>
                </div>
            `;
        }

        // DEFAULT: STATE A — NO SELF-CHECK CONFIGURED
        return `
            <div class="recovery-card-selfcheck bg-white border border-[#CDE9DA] rounded-3xl p-6 sm:p-8 space-y-4 shadow-xs relative overflow-hidden" data-tempo-ui="recovery-self-check">
                <div class="text-xs sm:text-sm font-semibold text-[#6F6B68]">
                    ${escapeHTML(greetingText)}
                </div>
                <div class="flex items-center space-x-2">
                    <span class="w-2.5 h-2.5 rounded-full bg-[#166545] inline-block"></span>
                    <span class="text-[11px] font-extrabold uppercase tracking-wider text-[#166545]">
                        ${window.t ? window.t('modes.recovery.selfCheck', {}, 'SELF-CHECK') : 'SELF-CHECK'}
                    </span>
                </div>
                <div class="space-y-1.5">
                    <h3 class="font-heading text-xl sm:text-2xl font-extrabold text-[#202124] tracking-tight">
                        ${window.t ? window.t('modes.recovery.selfCheckDesc', {}, 'What would you like to keep an eye on?') : 'What would you like to keep an eye on?'}
                    </h3>
                    <p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed max-w-lg">
                        Create your own check-in with the things that matter to you — stress signs, supportive habits, or anything else.
                    </p>
                </div>
                <div class="pt-3">
                    <button type="button" 
                            onclick="window.TempoMode.handleSelfCheckSetupClick()"
                            class="btn-primary px-5 py-2.5 rounded-xl font-bold text-xs sm:text-sm shadow-xs inline-flex items-center space-x-2 transition cursor-pointer">
                        <span>${window.t ? window.t('modes.recovery.setupSelfCheck', {}, 'Set up Self-check') : 'Set up Self-check'}</span>
                        <span>→</span>
                    </button>
                </div>
            </div>
        `;
    }

    // -------------------------------------------------------------------------
    // SHARED ECOSYSTEM FOR RECOVERY MODE
    // -------------------------------------------------------------------------
    function renderRecoverySharedEcosystem() {
        return `
            <div id="recovery-shared-ecosystem-container" data-tempo-ui="recovery-tools" class="space-y-8">
                ${window.TempoTools ? window.TempoTools.renderSectionHTML() : ''}
                ${window.TempoLearnSolve ? `<div id="rmode-learn-solve-container">${window.TempoLearnSolve.renderSectionHTML()}</div>` : ''}
            </div>
        `;
    }

    // Preserved for backwards compatibility (consolidated into shared ecosystem)
    function renderRecoverySupportRowHTML() {
        return '';
    }

    function renderRecentlyCard(recentlyState) {
        if (window.TempoSelfCheckHistory && typeof window.TempoSelfCheckHistory.renderRecentlyCard === 'function') {
            return window.TempoSelfCheckHistory.renderRecentlyCard();
        }

        if (recentlyState && recentlyState.type === 'NOT_ENOUGH') {
            return `
                <div class="recovery-card-recently bg-white border border-[#EAE4DF] rounded-3xl p-6 sm:p-7 space-y-4 shadow-xs flex flex-col justify-between h-full" data-tempo-ui="recovery-recently">
                    <div class="space-y-3">
                        <div class="flex items-center space-x-2">
                            <span class="text-[11px] font-extrabold uppercase tracking-wider text-[#6F6B68]">
                                ${window.t ? window.t('modes.recovery.recently', {}, 'RECENTLY') : 'RECENTLY'}
                            </span>
                        </div>
                        <h4 class="font-heading text-base sm:text-lg font-extrabold text-[#202124]">
                            ${window.t ? window.t('modes.recovery.recentlyJustStarted', {}, "You're just getting started.") : "You're just getting started."}
                        </h4>
                        <p class="text-xs text-[#6F6B68] leading-relaxed">
                            ${window.t ? window.t('modes.recovery.recentlyJustStartedDesc', {}, "There's not enough history to compare yet. Keep checking in at your own pace.") : "There's not enough history to compare yet. Keep checking in at your own pace."}
                        </p>
                    </div>
                    <div class="pt-4 border-t border-stone-100 text-[11px] text-[#6F6B68]">
                        <span>Look back history activates after 3 check-ins.</span>
                    </div>
                </div>
            `;
        }

        // DEFAULT: HONEST EMPTY STATE FOR PHASE 1
        return `
            <div class="recovery-card-recently bg-white border border-[#EAE4DF] rounded-3xl p-6 sm:p-7 space-y-4 shadow-xs flex flex-col justify-between h-full" data-tempo-ui="recovery-recently">
                <div class="space-y-3">
                    <div class="flex items-center space-x-2">
                        <span class="text-[11px] font-extrabold uppercase tracking-wider text-[#6F6B68]">
                            ${window.t ? window.t('modes.recovery.recently', {}, 'RECENTLY') : 'RECENTLY'}
                        </span>
                    </div>
                    <h4 class="font-heading text-base sm:text-lg font-extrabold text-[#202124]">
                        ${window.t ? window.t('modes.recovery.recentlyEmpty', {}, 'Nothing here yet.') : 'Nothing here yet.'}
                    </h4>
                    <p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed">
                        ${window.t ? window.t('modes.recovery.recentlyEmptyDesc', {}, "Once you start checking in, this space can help you look back at what you've been noticing over time.") : "Once you start checking in, this space can help you look back at what you've been noticing over time."}
                    </p>
                </div>
                <div class="pt-4 border-t border-stone-100 text-[11px] text-[#6F6B68]">
                    <span>${window.t ? window.t('modes.recovery.nothingNeedsRecorded', {}, 'Nothing needs to be recorded until you\'re ready.') : 'Nothing needs to be recorded until you\'re ready.'}</span>
                </div>
            </div>
        `;
    }

    function renderRecoveryNoteCard() {
        if (window.TempoRecoveryNote && typeof window.TempoRecoveryNote.renderHomeCard === 'function') {
            return window.TempoRecoveryNote.renderHomeCard();
        }
        return '';
    }

    function renderWeeklyReviewShell(isReady, reviewData) {
        if (!reviewData) {
            if (window.TempoWeeklyReview && typeof window.TempoWeeklyReview.getLatestEligibleWeek === 'function') {
                reviewData = window.TempoWeeklyReview.getLatestEligibleWeek();
            }
        }
        if (!reviewData) return '';

        const weekRange = reviewData.dateRange || 'Sep 21 – Sep 27';

        // Check if already reviewed
        const existingReflection = (window.TempoWeeklyReview && typeof window.TempoWeeklyReview.getReflectionForWeek === 'function')
            ? window.TempoWeeklyReview.getReflectionForWeek(reviewData.start)
            : null;

        if (existingReflection) {
            return `
                <div class="recovery-card-weeklyreview-quiet bg-[#F4FAF6] border border-[#CDE9DA] rounded-2xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-2xs">
                    <div class="flex items-center space-x-2">
                        <span class="text-xs font-extrabold uppercase tracking-wider text-[#166545]">WEEKLY REVIEW</span>
                        <span class="text-xs text-[#6F6B68] font-medium">• ${escapeHTML(weekRange)}</span>
                        <span class="text-xs font-semibold text-[#166545]">• ✓ Last week reviewed</span>
                    </div>
                    <button type="button" onclick="window.TempoWeeklyReview.open('${reviewData.start}', false)"
                            class="text-xs font-bold text-[#166545] hover:text-[#0E4A32] underline cursor-pointer self-start sm:self-auto">
                        View review →
                    </button>
                </div>
            `;
        }

        if (!isReady) return ''; // Hidden when dismissed or ineligible

        return `
            <div class="recovery-card-weeklyreview bg-gradient-to-br from-[#F4FAF6] to-[#EDF7F1] border border-[#CDE9DA] rounded-3xl p-6 sm:p-7 space-y-4 shadow-xs" data-tempo-ui="recovery-weekly-review">
                <div class="flex items-center space-x-2">
                    <span class="text-xs font-extrabold uppercase tracking-wider text-[#166545]">
                        YOUR WEEKLY REVIEW IS READY
                    </span>
                    <span class="text-xs text-[#6F6B68] font-medium">• ${escapeHTML(weekRange)}</span>
                </div>
                <div class="space-y-1">
                    <h4 class="font-heading text-lg font-bold text-[#202124]">A look back at what you checked in with</h4>
                    <p class="text-xs sm:text-sm text-[#6F6B68] max-w-xl leading-relaxed">
                        A look back at what you checked in with, what you worked through, and how the week felt.
                    </p>
                </div>
                <div class="pt-2 flex flex-wrap items-center gap-3">
                    <button onclick="if(window.TempoWeeklyReview && window.TempoWeeklyReview.open) { window.TempoWeeklyReview.open('${reviewData.start}', true); }"
                            class="px-5 py-2.5 rounded-xl font-bold text-xs sm:text-sm bg-[#166545] hover:bg-[#115237] text-white shadow-xs transition cursor-pointer">
                        Look back at my week →
                    </button>
                    <button onclick="window.TempoMode.dismissWeeklyReviewNotice()"
                            class="px-4 py-2.5 rounded-xl border border-[#CDE9DA] bg-white text-xs font-semibold text-stone-700 hover:bg-stone-50 transition cursor-pointer">
                        Maybe later
                    </button>
                </div>
            </div>
        `;
    }

    function renderRecoveryTodaySection(confirmedPlan, todayStr) {
        const allPlanned = (confirmedPlan && confirmedPlan.plannedTasks) ? confirmedPlan.plannedTasks : [];
        const todayTasks = allPlanned.filter(pt => pt.dayDate === todayStr);

        let contentHTML = '';

        if (todayTasks.length === 0) {
            contentHTML = `
                <div class="bg-white border border-[#EAE4DF] rounded-3xl p-6 sm:p-7 space-y-2 shadow-xs">
                    <h4 class="font-heading text-base sm:text-lg font-extrabold text-[#202124]">
                        Nothing planned for today.
                    </h4>
                    <p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed">
                        You don't need to fill the space. Take things at your own pace.
                    </p>
                </div>
            `;
        } else {
            const allTodayCompleted = todayTasks.every(pt => pt.task && pt.task.completed);
            if (allTodayCompleted) {
                contentHTML = `
                    <div class="bg-white border border-[#EAE4DF] rounded-3xl p-6 sm:p-7 space-y-2 shadow-xs">
                        <div class="flex items-center space-x-2 text-[#166545] font-bold text-sm sm:text-base">
                            <span>✓</span>
                            <span>You're done with today's plan.</span>
                        </div>
                        <p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed">
                            Rest and recovery are an essential part of the process. No need to rush into tomorrow's work.
                        </p>
                    </div>
                `;
            } else {
                let activeItem = todayTasks.find(pt => pt.task && pt.task.isInProgress && !pt.task.completed);
                const isContinue = !!activeItem;
                if (!activeItem) {
                    activeItem = todayTasks.find(pt => pt.task && !pt.task.completed);
                }

                if (activeItem && activeItem.task) {
                    const task = activeItem.task;
                    let nextActionText = "Begin focused work block.";
                    if (task.subtasks && task.subtasks.length > 0) {
                        const incompleteSubtasks = task.subtasks.filter(s => !s.completed);
                        nextActionText = incompleteSubtasks.length > 0 ? `Next: ${incompleteSubtasks[0].title}` : (task.description || "All preliminary steps completed.");
                    } else if (task.description) {
                        nextActionText = task.description;
                    }

                    const durationText = task.isUnknownDuration ? "Time not estimated" : `~ ${task.durationLabel || '45 min'}`;

                    contentHTML = `
                        <div class="bg-white border border-[#EAE4DF] rounded-3xl p-6 sm:p-7 space-y-4 shadow-xs">
                            <div class="flex items-center justify-between">
                                <span class="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold ${isContinue ? 'bg-[#FFE9DC] text-[#B83D08]' : 'bg-stone-100 text-stone-700'} uppercase tracking-wider">
                                    ${isContinue ? 'CONTINUE' : 'UP NEXT'}
                                </span>
                                <span class="text-xs text-[#6F6B68] font-medium">${escapeHTML(durationText)}</span>
                            </div>

                            <div class="space-y-1">
                                <h4 class="font-heading text-lg sm:text-xl font-extrabold text-[#202124]">
                                    ${escapeHTML(task.name)}
                                </h4>
                                <p class="text-xs sm:text-sm text-[#6F6B68]">
                                    ${escapeHTML(nextActionText)}
                                </p>
                            </div>

                            <div class="pt-2 flex flex-wrap items-center gap-3">
                                <button onclick="window.TempoMode.startTaskFocus('${task.id}')"
                                        class="btn-primary px-5 py-2.5 rounded-xl font-bold text-xs sm:text-sm shadow-xs inline-flex items-center space-x-2 transition cursor-pointer">
                                    <span>${isContinue ? 'Continue' : 'Focus on this task'}</span>
                                    <span>→</span>
                                </button>
                                <button onclick="window.TempoApp.navigateTo('plan-workspace'); if (window.TempoPlanWorkspace && window.TempoPlanWorkspace.selectTask) { window.TempoPlanWorkspace.selectTask('${task.id}'); }"
                                        class="px-4 py-2.5 rounded-xl border border-[#EAE4DF] text-xs font-bold text-[#202124] bg-white hover:bg-stone-50 transition shadow-xs cursor-pointer inline-flex items-center space-x-1.5">
                                    <span>View task</span>
                                    <span>→</span>
                                </button>
                            </div>
                        </div>
                    `;
                }
            }
        }

        return `
            <div id="recovery-today-section" class="recovery-section-today space-y-3 pt-1" data-tempo-ui="recovery-today">
                <div class="flex items-center justify-between">
                    <div class="flex items-center space-x-2">
                        <h3 class="font-heading text-lg sm:text-xl font-extrabold text-[#202124]">
                            Today
                        </h3>
                        <span class="text-xs text-[#6F6B68] font-medium hidden sm:inline">• Shared academic plan</span>
                    </div>
                    <button onclick="window.TempoApp.navigateTo('plan-workspace');"
                            class="text-xs font-bold text-[#166545] hover:text-[#0E4A32] flex items-center space-x-1 transition cursor-pointer">
                        <span>View / Edit Plan</span>
                        <span>→</span>
                    </button>
                </div>
                ${contentHTML}
            </div>
        `;
    }

    function renderRecoveryPostsSection() {
        const allPosts = (window.TempoCommunity && window.TempoCommunity.getAllPosts)
            ? window.TempoCommunity.getAllPosts()
            : [];

        let previewPosts = allPosts.filter(p => p.tag === '#Recovery' || p.tag === '#MentalHealth');
        if (previewPosts.length < 2) {
            previewPosts = allPosts.slice(0, 2);
        } else {
            previewPosts = previewPosts.slice(0, 2);
        }

        const postsCardsHTML = (previewPosts.length > 0 && window.TempoCommunity && window.TempoCommunity.renderPostCardHTML)
            ? previewPosts.map(p => window.TempoCommunity.renderPostCardHTML(p)).join('')
            : '';

        return `
            <div class="recovery-section-posts space-y-4 pt-2" data-tempo-ui="recovery-posts">
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
                            onclick="if (window.TempoCommunity) { window.TempoCommunity.openCommunityModal(); }" 
                            class="text-xs font-bold text-[#166545] hover:text-[#0E4A32] flex items-center space-x-1 transition cursor-pointer">
                        <span>See all posts</span>
                        <span>→</span>
                    </button>
                </div>

                <!-- Social Post Previews -->
                <div id="recovery-community-posts-list" class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    ${postsCardsHTML}
                </div>
            </div>
        `;
    }

    // =========================================================================
    // TASK & PLAN INTERACTIONS
    // =========================================================================

    function toggleTaskCompletion(taskId) {
        let isNowCompleted = false;
        if (window.TempoEmergencyFlow && window.TempoEmergencyFlow.toggleTaskCompleted) {
            isNowCompleted = window.TempoEmergencyFlow.toggleTaskCompleted(taskId);
        } else if (window.TempoPlanStore && window.TempoPlanStore.getActivePlan) {
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
            const taskItem = confirmedPlan?.plannedTasks?.find(pt => pt.task && pt.task.id === taskId);
            if (taskItem && taskItem.task && taskItem.task.name) {
                const taskNameEl = document.getElementById('focus-task-name');
                if (taskNameEl) {
                    taskNameEl.textContent = taskItem.task.name;
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

    // =========================================================================
    // HELPER & VALIDATION UTILITIES
    // =========================================================================

    function getTodayISOString() {
        const now = new Date();
        const y = now.getFullYear();
        const m = String(now.getMonth() + 1).padStart(2, '0');
        const d = String(now.getDate()).padStart(2, '0');
        return `${y}-${m}-${d}`;
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
        getMode,
        getCurrentMode: getMode,
        getPendingMode,
        hasPendingMode,
        getModeDisplayName,
        requestMode,
        handleAuthSuccess,
        setMode,
        selectModeOption,
        renderShellIndicator,
        openChangeModeModal,
        closeChangeModeModal,
        toggleModeDropdown,
        toggleNavbarModeDropdown,
        closeAllModeDropdowns,
        selectModeFromDropdown,
        renderEmodeHome,
        renderEmodePrimarySection,
        renderRmodeHome,
        renderUmodeHome,
        renderDmodeHome,
        renderEntryHome,
        renderEntryHomeHTML,
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
        handleSelfCheckSetupClick,
        handleSelfCheckAction,
        getRecentlyState,
        setRecentlyState,
        checkIsWeeklyReviewReady,
        setWeeklyReviewReady,
        dismissWeeklyReviewNotice,
        dismissRecoveryIntro,
        toggleTaskCompletion,
        startTaskFocus,
        stopForToday,
        keepWorkingToday,
        dismissStaleWarning,
        getSafeGreetingInfo,
        EPLAN_STATES
    };
})();

