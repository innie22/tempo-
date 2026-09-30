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

    // Single centralized source of truth for active mode
    let currentMode = MODES.DEFAULT;

    // Remembers intended mode across the authentication gate
    let pendingMode = null;

    // Session-level flags to prevent repeating dismissed alerts
    let sessionFlags = {
        dismissedStaleWarning: false,
        dismissedTimeEndedToday: false
    };

    function init() {
        // Load persisted mode safely from localStorage
        try {
            const savedMode = localStorage.getItem('tempo_current_mode');
            const authState = window.TempoAuth && typeof window.TempoAuth.getAuthState === 'function'
                ? window.TempoAuth.getAuthState()
                : 'AUTH_LOADING';
            const isAuthenticated = window.TempoAuth && !!window.TempoAuth.getCurrentUser();
            const hasActivePlan = window.TempoPlanStore && typeof window.TempoPlanStore.hasActivePlan === 'function' && window.TempoPlanStore.hasActivePlan('emergency');

            if (savedMode && Object.values(MODES).includes(savedMode)) {
                // If auth is still loading, NEVER reset saved mode!
                if (authState === 'AUTH_LOADING') {
                    currentMode = savedMode;
                } else if (!isAuthenticated && savedMode !== MODES.DEFAULT) {
                    // Confirmed anonymous user
                    currentMode = MODES.DEFAULT;
                    localStorage.setItem('tempo_current_mode', MODES.DEFAULT);
                } else {
                    currentMode = savedMode;
                }
            }

            if (hasActivePlan && isAuthenticated && currentMode === MODES.DEFAULT) {
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
            label.textContent = 'Urgent Mode';
        } else if (currentMode === MODES.RECOVERY) {
            badge.className = 'px-2.5 py-1 rounded-full text-xs font-bold bg-[#EDF7F1] text-[#166545] flex items-center space-x-1.5 shadow-sm';
            icon.textContent = '🌱';
            label.textContent = 'Recovery Mode';
        } else if (currentMode === MODES.UNCLEAR) {
            badge.className = 'px-2.5 py-1 rounded-full text-xs font-bold bg-[#FEF7EC] text-[#9A5B13] flex items-center space-x-1.5 shadow-sm';
            icon.textContent = '🧭';
            label.textContent = 'Unclear Mode';
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
                            <div class="text-xs font-bold text-[#202124] group-hover:text-[#FF6B2C] transition-colors">Urgent Mode</div>
                            <div class="text-[11px] text-[#6F6B68]">Handle what's urgent</div>
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
                            <div class="text-xs font-bold text-[#202124] group-hover:text-[#166545] transition-colors">Recovery Mode</div>
                            <div class="text-[11px] text-[#6F6B68]">Slow down and recover</div>
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
                            <div class="text-xs font-bold text-[#202124] group-hover:text-[#9A5B13] transition-colors">Unclear Mode</div>
                            <div class="text-[11px] text-[#6F6B68]">Figure out what's going on</div>
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
                            <div class="text-xs font-bold text-[#202124] group-hover:text-stone-900 transition-colors">Take a break from modes</div>
                            <div class="text-[11px] text-[#6F6B68]">Return to the default experience</div>
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

    function restoreDefaultHome() {
        applyModeVisibility(MODES.DEFAULT);
        if (window.TempoCommunity && typeof window.TempoCommunity.renderHomepagePreview === 'function') {
            window.TempoCommunity.renderHomepagePreview();
        }
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
            return { name: 'there', greetingText: 'Hi there 👋', isFallback: true };
        }

        // 1) preferred_name / display_name
        const pref = profile.preferred_name || profile.display_name;
        if (pref && isCleanShortName(pref)) {
            const clean = formatCapitalized(pref);
            return { name: clean, greetingText: `Hi, ${clean} 👋`, isFallback: false };
        }

        // 2) first_name
        const first = profile.first_name;
        if (first && isCleanShortName(first)) {
            const clean = formatCapitalized(first);
            return { name: clean, greetingText: `Hi, ${clean} 👋`, isFallback: false };
        }

        // 3) clean short extracted from full_name
        const full = profile.full_name;
        if (full && typeof full === 'string') {
            const firstToken = full.trim().split(/\s+/)[0];
            if (firstToken && isCleanShortName(firstToken)) {
                const clean = formatCapitalized(firstToken);
                return { name: clean, greetingText: `Hi, ${clean} 👋`, isFallback: false };
            }
        }

        // 4) Fallback
        return { name: 'there', greetingText: 'Hi there 👋', isFallback: true };
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

        // Render appropriate view according to state
        emodeBox.innerHTML = `
            ${renderEmodeHeader()}
            ${renderStateBody(activeHomeState, { confirmedPlan, currentStage, availabilityDays, todayStr, greetingInfo })}
        `;

        // Trigger community posts preview sync for urgent feed
        if (window.TempoCommunity && typeof window.TempoCommunity.renderUrgentPreview === 'function') {
            window.TempoCommunity.renderUrgentPreview();
        }
    }

    function renderEmodeHeader() {
        const todayObj = new Date();
        const formattedDate = todayObj.toLocaleDateString('en-US', {
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
                                onclick="window.TempoMode.toggleModeDropdown(event)" 
                                class="px-3.5 py-1.5 rounded-full text-xs font-bold bg-[#FFE9DC] text-[#B83D08] hover:bg-[#FFDFC9] border border-[#FFD2BA] transition flex items-center space-x-1.5 shadow-xs cursor-pointer"
                                aria-haspopup="true"
                                aria-expanded="false"
                                title="Switch Tempo Mode">
                            <span>⚡</span>
                            <span class="font-extrabold">Urgent Mode</span>
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

    function renderStateBody(state, ctx) {
        const { confirmedPlan, currentStage, availabilityDays, todayStr, greetingInfo } = ctx;

        switch (state) {
            case 'PLAN_INCOMPLETE':
                return renderStatePlanIncomplete(currentStage);

            case 'PLAN_COMPLETE':
                return renderStatePlanComplete(confirmedPlan);

            case 'PLAN_STALE':
                return renderStatePlanStale(confirmedPlan, todayStr);

            case 'TIME_ENDED_WITH_INCOMPLETE_WORK':
                return renderStateTimeEnded(confirmedPlan, todayStr);

            case 'TODAY_COMPLETE':
                return renderStateTodayComplete(confirmedPlan, todayStr);

            case 'NO_WORK_TODAY':
                return renderStateNoWorkToday(confirmedPlan, todayStr);

            case 'ACTIVE_TODAY':
            default:
                return renderStateActiveToday(confirmedPlan, todayStr, greetingInfo);
        }
    }

    // -------------------------------------------------------------------------
    // STATE A: PLAN_INCOMPLETE
    // -------------------------------------------------------------------------
    function renderStatePlanIncomplete(currentStage) {
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
            <div class="space-y-8">
                <!-- Resume Card -->
                <div class="bg-white border-2 border-dashed border-[#FF6B2C]/50 rounded-3xl p-6 sm:p-8 space-y-5 shadow-xs">
                    <div class="space-y-2">
                        <span class="px-3 py-1 rounded-full text-[11px] font-extrabold bg-[#FFE9DC] text-[#B83D08] uppercase tracking-wider">
                            YOUR URGENT PLAN
                        </span>
                        <h3 class="font-heading text-xl sm:text-2xl font-extrabold text-[#202124]">
                            You're still setting up your plan.
                        </h3>
                        <p class="text-xs sm:text-sm text-[#6F6B68] max-w-lg leading-relaxed">
                            Your urgent plan setup is in progress at step: <strong class="text-[#202124]">${escapeHTML(currentStageTitle)}</strong>.
                            All of your task entries and estimates are safely preserved.
                        </p>
                    </div>

                    <div class="pt-2 flex flex-wrap items-center gap-3">
                        <button onclick="window.TempoApp.navigateTo('emergency'); window.TempoEmergencyFlow.goToStage('${currentStage}');"
                                class="btn-primary px-6 py-3 rounded-xl font-bold text-xs sm:text-sm shadow-md inline-flex items-center space-x-2 transition cursor-pointer">
                            <span>Continue building my plan</span>
                            <span>→</span>
                        </button>
                        <button onclick="window.TempoMode.openChangeModeModal()" 
                                class="px-4 py-3 rounded-xl border border-gray-200 text-xs font-semibold text-gray-700 bg-white hover:bg-stone-50 transition cursor-pointer">
                            Switch mode
                        </button>
                    </div>
                </div>

                <!-- Support Row -->
                ${renderSupportRowHTML()}

                <!-- Tempo Posts -->
                ${renderTempoPostsSection()}
            </div>
        `;
    }

    // -------------------------------------------------------------------------
    // STATE G: PLAN_COMPLETE
    // -------------------------------------------------------------------------
    function renderStatePlanComplete(confirmedPlan) {
        const totalTasks = confirmedPlan?.plannedTasks?.length || 0;

        return `
            <div class="space-y-8">
                <div class="bg-gradient-to-br from-[#EDF7F1] via-white to-[#F6FAF8] border border-[#CDE9DA] rounded-3xl p-8 sm:p-10 space-y-6 text-center shadow-xs">
                    <div class="w-16 h-16 bg-[#EDF7F1] text-[#166545] border border-[#CDE9DA] rounded-2xl flex items-center justify-center mx-auto text-3xl shadow-sm">
                        🎉
                    </div>
                    <div class="space-y-2 max-w-md mx-auto">
                        <span class="text-xs font-extrabold uppercase tracking-widest text-[#166545]">ACUTE CRISIS CLEARED</span>
                        <h3 class="font-heading text-2xl sm:text-3xl font-extrabold text-[#202124]">
                            Your Urgent Plan is complete.
                        </h3>
                        <p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed">
                            No urgent tasks are waiting in this plan. You worked through ${totalTasks} planned task${totalTasks === 1 ? '' : 's'} step by step.
                        </p>
                    </div>

                    <!-- Mode Recommendation Suggestion (Never forced) -->
                    <div class="p-4 bg-white/90 border border-[#CDE9DA] rounded-2xl max-w-md mx-auto text-left flex items-start space-x-3 text-xs text-[#166545]">
                        <span class="text-lg">🌱</span>
                        <div class="space-y-1">
                            <p class="font-bold">Tempo Recommendation:</p>
                            <p class="text-[#202124] leading-relaxed">Your workload has eased up. Shifting toward <strong>Recovery Mode</strong> can help you restore energy and rebuild a sustainable pace.</p>
                        </div>
                    </div>

                    <div class="pt-2 flex flex-col sm:flex-row items-center justify-center gap-3">
                        <button onclick="window.TempoMode.setMode('recovery')" 
                                class="btn-primary px-6 py-3 rounded-xl font-bold text-xs sm:text-sm shadow-md transition cursor-pointer">
                            Shift to Recovery Mode →
                        </button>
                        <button onclick="window.TempoMode.openChangeModeModal()" 
                                class="px-5 py-3 rounded-xl border border-gray-200 text-xs font-semibold text-gray-700 bg-white hover:bg-stone-50 transition cursor-pointer">
                            Change mode
                        </button>
                        <button onclick="window.TempoApp.showToast('Remaining in Urgent Mode.')" 
                                class="px-4 py-3 text-xs text-[#6F6B68] hover:text-[#202124] underline cursor-pointer">
                            Stay in Urgent Mode
                        </button>
                    </div>
                </div>

                <!-- Support Row -->
                ${renderSupportRowHTML()}

                <!-- Tempo Posts -->
                ${renderTempoPostsSection()}
            </div>
        `;
    }

    // -------------------------------------------------------------------------
    // STATE F: PLAN_STALE
    // -------------------------------------------------------------------------
    function renderStatePlanStale(confirmedPlan, todayStr) {
        const staleTasks = (confirmedPlan?.plannedTasks || []).filter(pt => {
            return pt.dayDate && pt.dayDate < todayStr && (!pt.task || !pt.task.completed);
        });

        return `
            <div class="space-y-8">
                <div class="bg-amber-50 border border-amber-200 rounded-3xl p-6 sm:p-8 space-y-4 shadow-xs">
                    <div class="flex items-start space-x-3.5">
                        <span class="text-2xl mt-0.5">⚠️</span>
                        <div class="space-y-1">
                            <span class="text-[11px] font-bold uppercase tracking-wider text-amber-800">SCHEDULE UPDATE NEEDED</span>
                            <h3 class="font-heading text-xl sm:text-2xl font-bold text-amber-950">
                                Your plan needs an update.
                            </h3>
                            <p class="text-xs sm:text-sm text-amber-900 leading-relaxed">
                                Some planned work dates have passed while tasks are still unfinished. We don't reschedule automatically—let's review and adjust your plan calmly together.
                            </p>
                        </div>
                    </div>

                    <div class="p-3.5 bg-white/80 rounded-2xl border border-amber-200/70 text-xs text-amber-950 space-y-1.5">
                        <div class="font-bold text-stone-700 uppercase text-[10px] tracking-wider">Unfinished from past dates:</div>
                        ${staleTasks.map(t => `
                            <div class="flex items-center justify-between">
                                <span class="font-semibold">• ${escapeHTML(t.task.name)}</span>
                                <span class="text-stone-500 text-[11px]">Was scheduled: ${escapeHTML(t.dayLabel || t.dayDate)}</span>
                            </div>
                        `).join('')}
                    </div>

                    <div class="pt-2 flex flex-wrap items-center gap-3">
                        <button onclick="window.TempoApp.navigateTo('plan-workspace');"
                                class="btn-primary px-5 py-2.5 rounded-xl font-bold text-xs shadow-sm transition cursor-pointer">
                            Review & update plan →
                        </button>
                        <button onclick="window.TempoMode.dismissStaleWarning()" 
                                class="px-4 py-2.5 rounded-xl border border-amber-300 text-xs font-semibold text-amber-900 bg-white hover:bg-amber-100/50 transition cursor-pointer">
                            Dismiss for now
                        </button>
                    </div>
                </div>

                <!-- Support Row -->
                ${renderSupportRowHTML()}

                <!-- Tempo Posts -->
                ${renderTempoPostsSection()}
            </div>
        `;
    }

    // -------------------------------------------------------------------------
    // STATE E: TIME_ENDED_WITH_INCOMPLETE_WORK
    // -------------------------------------------------------------------------
    function renderStateTimeEnded(confirmedPlan, todayStr) {
        const todayTasks = (confirmedPlan?.plannedTasks || []).filter(pt => pt.dayDate === todayStr);
        const topUnfinished = todayTasks.find(pt => !pt.task.completed) || todayTasks[0];
        const taskName = topUnfinished?.task?.name || 'Your planned work';

        // Check if stopping causes deadline conflict
        const hasDeadlineRisk = topUnfinished?.task?.hasDeadline && (
            topUnfinished.task.deadlineDate === todayStr ||
            topUnfinished.task.deadlineDate < todayStr
        );

        return `
            <div class="space-y-8">
                <div class="bg-[#FFF8F2] border border-[#FFD2BA] rounded-3xl p-6 sm:p-8 space-y-5 shadow-xs">
                    <div class="flex items-start space-x-3.5">
                        <span class="text-2xl mt-0.5">⏰</span>
                        <div class="space-y-1">
                            <span class="text-[11px] font-bold uppercase tracking-wider text-[#B83D08]">PLANNED WINDOW ENDED</span>
                            <h3 class="font-heading text-xl sm:text-2xl font-bold text-[#202124]">
                                Your planned work time for today has ended.
                            </h3>
                            <p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed">
                                <strong class="text-[#202124]">${escapeHTML(taskName)}</strong> is still in progress.
                            </p>
                        </div>
                    </div>

                    ${hasDeadlineRisk ? `
                        <div class="p-3.5 bg-rose-50 border border-rose-200 rounded-2xl text-xs text-rose-900 space-y-1">
                            <div class="font-bold flex items-center space-x-1">
                                <span>⚠️</span>
                                <span>Upcoming Deadline Notice:</span>
                            </div>
                            <p>This task is due tonight or early tomorrow. If you choose to stop now, you may want to open your plan and allocate a morning block tomorrow.</p>
                        </div>
                    ` : ''}

                    <div class="space-y-2 pt-1">
                        <span class="text-xs font-bold text-[#202124]">What would you like to do?</span>
                        <div class="flex flex-wrap items-center gap-3">
                            <button onclick="window.TempoMode.stopForToday()" 
                                    class="px-5 py-2.5 rounded-xl bg-stone-100 hover:bg-stone-200 text-stone-800 text-xs font-bold transition cursor-pointer">
                                Stop for today
                            </button>
                            <button onclick="window.TempoMode.keepWorkingToday()" 
                                    class="btn-primary px-5 py-2.5 rounded-xl text-xs font-bold shadow-sm transition cursor-pointer">
                                Keep working
                            </button>
                            <button onclick="window.TempoApp.navigateTo('plan-workspace');" 
                                    class="px-4 py-2.5 rounded-xl border border-gray-200 text-xs font-semibold text-gray-700 bg-white hover:bg-stone-50 transition cursor-pointer">
                                Adjust my plan
                            </button>
                        </div>
                    </div>
                </div>

                <!-- Support Row -->
                ${renderSupportRowHTML()}

                <!-- Tempo Posts -->
                ${renderTempoPostsSection()}
            </div>
        `;
    }

    // -------------------------------------------------------------------------
    // STATE C: TODAY_COMPLETE
    // -------------------------------------------------------------------------
    function renderStateTodayComplete(confirmedPlan, todayStr) {
        // Find next planned date with tasks
        const futureTasks = (confirmedPlan?.plannedTasks || []).filter(pt => {
            return pt.dayDate > todayStr && (!pt.task || !pt.task.completed);
        });

        const nextItem = futureTasks[0];
        const nextScheduleText = nextItem
            ? `${nextItem.dayLabel || nextItem.dayDate}${nextItem.startTime ? ` · ${nextItem.startTime}` : ''}`
            : 'No further dates scheduled';

        return `
            <div class="space-y-8">
                <div class="bg-white border border-[#EAE4DF] rounded-3xl p-6 sm:p-8 space-y-5 shadow-xs">
                    <div class="flex items-center space-x-2">
                        <span class="w-6 h-6 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold text-xs">✓</span>
                        <span class="text-[11px] font-extrabold uppercase tracking-wider text-emerald-800">TODAY'S WORK DONE</span>
                    </div>

                    <div class="space-y-1">
                        <h3 class="font-heading text-2xl sm:text-3xl font-extrabold text-[#202124]">
                            You're done for today.
                        </h3>
                        <p class="text-xs sm:text-sm text-[#6F6B68]">
                            You've completed what you planned for today. Protect your rest.
                        </p>
                    </div>

                    <div class="p-4 bg-[#FFFDFB] border border-[#EAE4DF] rounded-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
                        <div class="space-y-0.5">
                            <span class="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Next planned work:</span>
                            <div class="font-bold text-sm text-[#202124]">${escapeHTML(nextScheduleText)}</div>
                            ${nextItem ? `<p class="text-[#6F6B68] text-[11px]">${escapeHTML(nextItem.task.name)}</p>` : ''}
                        </div>
                        ${nextItem ? `
                            <button onclick="window.TempoApp.navigateTo('plan-workspace');"
                                    class="px-4 py-2 rounded-xl border border-gray-200 bg-white font-semibold text-xs text-gray-700 hover:bg-stone-50 transition self-start sm:self-auto cursor-pointer">
                                View tomorrow →
                            </button>
                        ` : ''}
                    </div>
                </div>

                <!-- Support Row -->
                ${renderSupportRowHTML()}

                <!-- Tempo Posts -->
                ${renderTempoPostsSection()}
            </div>
        `;
    }

    // -------------------------------------------------------------------------
    // STATE D: NO_WORK_TODAY
    // -------------------------------------------------------------------------
    function renderStateNoWorkToday(confirmedPlan, todayStr) {
        const upcomingTasks = (confirmedPlan?.plannedTasks || []).filter(pt => pt.dayDate > todayStr);
        const nextItem = upcomingTasks[0];
        const nextDateLabel = nextItem ? (nextItem.dayLabel || nextItem.dayDate) : 'a future date';

        return `
            <div class="space-y-8">
                <div class="bg-white border border-[#EAE4DF] rounded-3xl p-6 sm:p-8 space-y-4 shadow-xs">
                    <div class="space-y-1">
                        <span class="text-[11px] font-extrabold uppercase tracking-wider text-[#6F6B68]">SCHEDULE OVERVIEW</span>
                        <h3 class="font-heading text-2xl font-bold text-[#202124]">
                            Nothing planned for today.
                        </h3>
                        <p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed">
                            Your Urgent Plan continues on <strong>${escapeHTML(nextDateLabel)}</strong>.
                        </p>
                    </div>

                    <div class="pt-2 flex items-center space-x-3">
                        <button onclick="window.TempoApp.navigateTo('plan-workspace');"
                                class="px-4 py-2.5 rounded-xl border border-gray-200 text-xs font-semibold text-gray-700 hover:bg-stone-50 transition cursor-pointer">
                            View Plan Schedule →
                        </button>
                    </div>
                </div>

                <!-- Support Row -->
                ${renderSupportRowHTML()}

                <!-- Tempo Posts -->
                ${renderTempoPostsSection()}
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
            ? `Due ${formatHumanDeadline(nowItem.task.deadlineDate, nowItem.task.deadlineTime)}`
            : "No fixed deadline";

        const durationText = nowItem
            ? (nowItem.task.isUnknownDuration ? "Time not estimated" : `~ ${nowItem.task.durationLabel || '45 min'}`)
            : "~ 45 min";

        // Check for "Needs Attention" items (ONLY if actual issues exist!)
        const needsAttentionItems = checkNeedsAttentionIssues(confirmedPlan, todayStr);

        return `
            <div class="space-y-8">
                <!-- Main Asymmetric Grid: ~65% Left / ~35% Right on Desktop -->
                <div class="urgent-home-main-grid">
                    <!-- LEFT COLUMN -->
                    <div class="urgent-left-col">
                        <!-- Priority #1: YOUR TASK FOR NOW -->
                        ${nowItem ? `
                            <div class="urgent-card-now bg-gradient-to-br from-[#FFF9F5] via-[#FFF3EB] to-[#FFEFE6] border border-[#FFD2BA] rounded-3xl p-6 sm:p-8 space-y-4 shadow-sm relative overflow-hidden">
                                <!-- Greeting directly above YOUR TASK FOR NOW -->
                                <div class="relative z-10 text-xs sm:text-sm font-semibold text-[#6F6B68]">
                                    ${escapeHTML(greetingInfo ? greetingInfo.greetingText : 'Hi there 👋')}
                                </div>

                                <div class="relative z-10 flex items-center justify-between">
                                    <div class="flex items-center space-x-2">
                                        <span class="w-2.5 h-2.5 rounded-full bg-[#FF6B2C] animate-pulse inline-block"></span>
                                        <span class="text-[11px] font-extrabold uppercase tracking-wider text-[#B83D08]">
                                            YOUR TASK FOR NOW
                                        </span>
                                    </div>
                                    <span class="px-3 py-1 rounded-full text-[10px] font-extrabold bg-[#FF6B2C] text-white tracking-wider shadow-xs">
                                        NOW
                                    </span>
                                </div>

                                <div class="relative z-10 space-y-1.5">
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
                                        <span>Focus on this task →</span>
                                    </button>
                                    <button onclick="window.TempoApp.navigateTo('plan-workspace'); if (window.TempoPlanWorkspace && window.TempoPlanWorkspace.selectTask) { window.TempoPlanWorkspace.selectTask('${nowItem.task.id}'); }"
                                            class="px-4 py-2.5 rounded-xl border border-[#EAE4DF] text-xs font-bold text-[#202124] bg-white hover:bg-stone-50 transition shadow-xs cursor-pointer inline-flex items-center space-x-1.5">
                                        <span>View task</span>
                                        <span>→</span>
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

                        <!-- Support Row: Feeling Overwhelmed + Focus Now -->
                        ${renderSupportRowHTML()}
                    </div>

                    <!-- RIGHT COLUMN: Priority #2 - Your plan for today -->
                    <div class="urgent-right-col bg-white border border-[#EAE4DF] rounded-3xl p-6 sm:p-7 space-y-5 shadow-xs flex flex-col justify-between">
                        <div class="space-y-4">
                            <!-- Header -->
                            <div class="flex items-center justify-between pb-1">
                                <h3 class="font-heading text-lg sm:text-xl font-extrabold text-[#202124]">
                                    Your plan for today
                                </h3>
                                <button onclick="window.TempoApp.navigateTo('plan-workspace');"
                                        class="text-xs font-bold text-[#FF6B2C] hover:text-[#B83D08] flex items-center space-x-1 transition cursor-pointer">
                                    <span>View / Edit Plan</span>
                                    <span>→</span>
                                </button>
                            </div>

                            <!-- Progress Header & Bar -->
                            <div class="space-y-1.5">
                                <div class="flex items-center justify-between text-xs">
                                    <span class="text-[#6F6B68] font-medium">${completedTodayCount} of ${todayTasks.length} completed</span>
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
                                    const isUpNext = !isDone && !isNow;
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
                                        badgeHTML = `<span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">Completed</span>`;
                                    } else if (isNow) {
                                        badgeHTML = `<span class="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold bg-[#FFE9DC] text-[#B83D08]">NOW</span>`;
                                    } else {
                                        badgeHTML = `<span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-stone-100 text-stone-600">UP NEXT</span>`;
                                    }

                                    const timeDurationStr = `${item.startTime || ''}${item.startTime ? ' · ' : ''}~${item.task.isUnknownDuration ? 'Not estimated' : (item.task.durationLabel || '45 min')}`;

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
                    </div>
                </div>

                <!-- Tempo Posts Section -->
                ${renderTempoPostsSection()}
            </div>
        `;
    }

    // -------------------------------------------------------------------------
    // SUPPORT ROW COMPONENT (Feeling Overwhelmed + Focus Now)
    // -------------------------------------------------------------------------
    function renderSupportRowHTML() {
        return `
            <div class="urgent-support-row">
                <!-- Feeling Overwhelmed Card -->
                <div class="urgent-card-overwhelmed bg-gradient-to-br from-[#FFFBF7] to-[#FFF5EC] border border-[#FFD2BA] rounded-3xl p-5 space-y-4 shadow-xs relative overflow-hidden urgent-dot-pattern flex flex-col justify-between">
                    <div class="space-y-3 relative z-10">
                        <div class="w-10 h-10 rounded-2xl bg-[#FFE9DC] text-[#B83D08] flex items-center justify-center text-lg font-bold shadow-xs">
                            ⚡
                        </div>
                        <div>
                            <h4 class="font-heading text-base font-extrabold text-[#202124]">
                                Feeling overwhelmed?
                            </h4>
                            <p class="text-xs text-[#6F6B68] leading-relaxed mt-1">
                                Take a few minutes to calm things down and clear your head.
                            </p>
                        </div>
                    </div>
                    <div class="pt-2 flex flex-wrap items-center gap-2.5 relative z-10">
                        <button onclick="window.TempoStressRelief.openModal()"
                                class="btn-primary px-3.5 py-2 rounded-xl text-xs font-bold shadow-xs transition cursor-pointer">
                            Quick Stress Relief →
                        </button>
                        <button onclick="window.TempoTriage.openBoxBreathingModal()"
                                class="px-3 py-2 rounded-xl border border-[#FFD2BA] bg-white text-xs font-bold text-[#B83D08] hover:bg-[#FFF5EC] transition cursor-pointer flex items-center space-x-1">
                            <span>💨</span>
                            <span>Breathing</span>
                        </button>
                    </div>
                </div>

                <!-- Focus Now Card -->
                <div class="urgent-card-focus-now bg-white border border-[#EAE4DF] rounded-3xl p-5 space-y-4 shadow-xs flex flex-col justify-between">
                    <div class="space-y-3">
                        <div class="w-10 h-10 rounded-2xl bg-[#FFE9DC] text-[#FF6B2C] flex items-center justify-center text-lg font-bold shadow-xs">
                            🎯
                        </div>
                        <div>
                            <h4 class="font-heading text-base font-extrabold text-[#202124]">
                                Focus now
                            </h4>
                            <p class="text-xs text-[#6F6B68] leading-relaxed mt-1">
                                Start a Focus session at your own pace.
                            </p>
                        </div>
                    </div>
                    <div class="pt-2">
                        <button onclick="if (window.TempoFocusZone) { window.TempoFocusZone.openQuickEntry(); } else if (window.TempoTriage) { window.TempoTriage.launchFocusMode(); }"
                                class="w-full py-2.5 px-4 rounded-xl bg-[#FFF1E8] hover:bg-[#FFE5D4] text-[#B83D08] font-bold text-xs transition text-center shadow-xs cursor-pointer">
                            Start Focus →
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
            <div class="urgent-section-posts space-y-4 pt-2">
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
                            class="text-xs font-bold text-[#FF6B2C] hover:text-[#B83D08] flex items-center space-x-1 transition cursor-pointer">
                        <span>See all posts</span>
                        <span>→</span>
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
            <div class="space-y-8">
                <!-- Main Asymmetric Grid: ~65% Left / ~35% Right on Desktop -->
                <div class="recovery-home-main-grid">
                    <!-- LEFT COLUMN (~65%) -->
                    <div class="recovery-left-col">
                        ${renderSelfCheckCard(selfCheckState, greetingInfo)}
                        ${renderRecoverySupportRowHTML()}
                    </div>

                    <!-- RIGHT COLUMN (~35%) -->
                    <div class="recovery-right-col space-y-6">
                        ${renderRecoveryNoteCard()}
                        ${renderRecentlyCard(recentlyState)}
                    </div>
                </div>

                ${renderWeeklyReviewShell(isWeeklyReviewReady, latestEligibleWeek)}
                ${renderRecoveryTodaySection(confirmedPlan, todayStr)}
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

        const umodeBox = document.getElementById('umode-home-content');
        if (!umodeBox) return;

        const todayObj = new Date();
        const formattedDate = todayObj.toLocaleDateString('en-US', {
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
                            <span class="font-extrabold">Unclear Mode</span>
                            <span class="text-[10px] ml-0.5 opacity-80">▾</span>
                        </button>
                        <div id="home-mode-selector-dropdown" class="hidden absolute left-0 mt-2 w-72 sm:w-80 bg-white rounded-2xl shadow-xl border border-[#EAE4DF] z-50 overflow-hidden" role="menu"></div>
                    </div>
                    <div class="text-xs font-semibold text-[#8E8A85]">
                        ${formattedDate}
                    </div>
                </div>
            </div>

            <!-- Unclear Mode Content Card -->
            <div class="bg-white border border-[#FDE5BE] rounded-3xl p-8 sm:p-12 text-center space-y-6 shadow-sm">
                <div class="w-16 h-16 rounded-2xl bg-[#FEF7EC] text-[#9A5B13] border border-[#FDE5BE] flex items-center justify-center mx-auto text-2xl shadow-sm">
                    🧭
                </div>
                <div class="space-y-2 max-w-lg mx-auto">
                    <span class="text-xs font-extrabold uppercase tracking-widest text-[#9A5B13]">UNCLEAR MODE</span>
                    <h2 class="font-heading text-2xl sm:text-3xl font-extrabold text-[#202124]">Unclear Mode is being prepared</h2>
                    <p class="text-sm text-[#6F6B68] leading-relaxed">
                        We're designing a guided unpack flow to help you navigate when you feel off but can't clearly identify what you need right now.
                    </p>
                </div>
                <div class="pt-4 flex flex-col sm:flex-row items-center justify-center gap-3">
                    <button onclick="window.TempoMode.selectModeFromDropdown('default', 'home')" class="btn-primary px-6 py-2.5 rounded-xl text-xs sm:text-sm font-bold shadow-sm transition cursor-pointer">
                        ← Return to Default Tempo
                    </button>
                    <button onclick="window.TempoApp.navigateTo('stress-check')" class="px-5 py-2.5 rounded-xl text-xs sm:text-sm font-semibold text-gray-700 bg-white border border-gray-200 hover:bg-stone-50 transition cursor-pointer">
                        Take Self-Check in the Meantime
                    </button>
                </div>
            </div>
        `;
    }

    function renderActiveModeHome() {
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
        const formattedDate = todayObj.toLocaleDateString('en-US', {
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
                                onclick="window.TempoMode.toggleModeDropdown(event)" 
                                class="px-3.5 py-1.5 rounded-full text-xs font-bold bg-[#EDF7F1] text-[#166545] hover:bg-[#DDF0E5] border border-[#CDE9DA] transition flex items-center space-x-1.5 shadow-xs cursor-pointer"
                                aria-haspopup="true"
                                aria-expanded="false"
                                title="Switch Tempo Mode">
                            <span>🌱</span>
                            <span class="font-extrabold">Recovery Mode</span>
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
                            You're in Recovery Mode
                        </h4>
                        <p class="text-xs sm:text-sm text-[#2D6A4F] leading-relaxed max-w-2xl">
                            Nothing you need to complete here. Use this space to slow things down, check in when you want to, or simply take a little breathing room.
                        </p>
                    </div>
                </div>
                <button type="button" 
                        onclick="window.TempoMode.dismissRecoveryIntro()" 
                        class="px-4 py-2 bg-white hover:bg-stone-50 text-[#166545] border border-[#CDE9DA] font-bold text-xs rounded-xl shadow-xs shrink-0 self-start sm:self-auto transition cursor-pointer">
                    Got it
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
                <div class="recovery-card-selfcheck bg-white border border-[#CDE9DA] rounded-3xl p-6 sm:p-8 space-y-5 shadow-xs relative overflow-hidden">
                    <div class="text-xs sm:text-sm font-semibold text-[#6F6B68]">
                        ${escapeHTML(greetingText)}
                    </div>
                    <div class="flex items-center space-x-2">
                        <span class="w-2.5 h-2.5 rounded-full bg-[#166545] inline-block"></span>
                        <span class="text-[11px] font-extrabold uppercase tracking-wider text-[#166545]">
                            SELF-CHECK
                        </span>
                    </div>
                    <div class="space-y-1">
                        <h3 class="font-heading text-xl sm:text-2xl font-extrabold text-[#202124]">
                            How have things been today?
                        </h3>
                        <p class="text-xs text-[#6F6B68] font-medium">${streakCount} day check-in streak</p>
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
                            <span>Check in</span>
                            <span>→</span>
                        </button>
                        <button onclick="window.TempoMode.handleSelfCheckAction('manage')"
                                class="text-xs font-semibold text-[#166545] hover:text-[#0E4A32] transition cursor-pointer">
                            Manage Self-check
                        </button>
                        <span class="text-stone-300">·</span>
                        <button onclick="window.TempoMode.handleSelfCheckAction('history')"
                                class="text-xs font-semibold text-[#166545] hover:text-[#0E4A32] transition cursor-pointer">
                            View history
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
                <div class="recovery-card-selfcheck bg-white border border-[#CDE9DA] rounded-3xl p-6 sm:p-8 space-y-5 shadow-xs relative overflow-hidden">
                    <div class="text-xs sm:text-sm font-semibold text-[#6F6B68]">
                        ${escapeHTML(greetingText)}
                    </div>
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-2">
                            <span class="w-2.5 h-2.5 rounded-full bg-[#166545] inline-block"></span>
                            <span class="text-[11px] font-extrabold uppercase tracking-wider text-[#166545]">
                                SELF-CHECK
                            </span>
                        </div>
                        <span class="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#EDF7F1] text-[#166545] border border-[#CDE9DA]">
                            ✓ Checked in today
                        </span>
                    </div>
                    <div class="space-y-1">
                        <h3 class="font-heading text-xl sm:text-2xl font-extrabold text-[#202124]">
                            Checked in for today
                        </h3>
                        <p class="text-xs text-[#6F6B68] font-medium">${streakCount} day check-in streak</p>
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
                            <span>View today's check-in</span>
                            <span>→</span>
                        </button>
                        <div class="flex items-center space-x-2 text-xs font-semibold text-[#166545]">
                            <button onclick="window.TempoMode.handleSelfCheckAction('edit')" class="hover:text-[#0E4A32] transition cursor-pointer">Edit check-in</button>
                            <span class="text-stone-300">·</span>
                            <button onclick="window.TempoMode.handleSelfCheckAction('manage')" class="hover:text-[#0E4A32] transition cursor-pointer">Manage Self-check</button>
                            <span class="text-stone-300">·</span>
                            <button onclick="window.TempoMode.handleSelfCheckAction('history')" class="hover:text-[#0E4A32] transition cursor-pointer">History</button>
                        </div>
                    </div>
                </div>
            `;
        }

        // DEFAULT: STATE A — NO SELF-CHECK CONFIGURED
        return `
            <div class="recovery-card-selfcheck bg-white border border-[#CDE9DA] rounded-3xl p-6 sm:p-8 space-y-4 shadow-xs relative overflow-hidden">
                <div class="text-xs sm:text-sm font-semibold text-[#6F6B68]">
                    ${escapeHTML(greetingText)}
                </div>
                <div class="flex items-center space-x-2">
                    <span class="w-2.5 h-2.5 rounded-full bg-[#166545] inline-block"></span>
                    <span class="text-[11px] font-extrabold uppercase tracking-wider text-[#166545]">
                        SELF-CHECK
                    </span>
                </div>
                <div class="space-y-1.5">
                    <h3 class="font-heading text-xl sm:text-2xl font-extrabold text-[#202124] tracking-tight">
                        What would you like to keep an eye on?
                    </h3>
                    <p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed max-w-lg">
                        Create your own check-in with the things that matter to you — stress signs, supportive habits, or anything else.
                    </p>
                </div>
                <div class="pt-3">
                    <button type="button" 
                            onclick="window.TempoMode.handleSelfCheckSetupClick()"
                            class="btn-primary px-5 py-2.5 rounded-xl font-bold text-xs sm:text-sm shadow-xs inline-flex items-center space-x-2 transition cursor-pointer">
                        <span>Set up Self-check</span>
                        <span>→</span>
                    </button>
                </div>
            </div>
        `;
    }

    function renderRecoverySupportRowHTML() {
        return `
            <div class="recovery-support-row">
                <!-- Quick Relief Card -->
                <div class="recovery-card-quickrelief bg-gradient-to-br from-[#FFFBF7] to-[#FFF5EC] border border-[#FFD2BA] rounded-3xl p-5 space-y-4 shadow-xs flex flex-col justify-between">
                    <div class="space-y-3">
                        <div class="w-10 h-10 rounded-2xl bg-[#FFE9DC] text-[#B83D08] flex items-center justify-center text-lg font-bold shadow-xs">
                            🌿
                        </div>
                        <div>
                            <span class="text-[10px] font-extrabold uppercase tracking-wider text-[#B83D08]">
                                QUICK RELIEF
                            </span>
                            <h4 class="font-heading text-base font-extrabold text-[#202124] mt-0.5">
                                Need a few minutes to settle?
                            </h4>
                            <p class="text-xs text-[#6F6B68] leading-relaxed mt-1">
                                Take a moment to ease physical tension or slow down racing thoughts.
                            </p>
                        </div>
                    </div>
                    <div class="pt-2 flex flex-wrap items-center gap-2.5">
                        <button onclick="window.TempoStressRelief.openModal()"
                                class="btn-primary px-3.5 py-2 rounded-xl text-xs font-bold shadow-xs transition cursor-pointer">
                            Quick Stress Relief →
                        </button>
                        <button onclick="window.TempoTriage.openBoxBreathingModal()"
                                class="px-3 py-2 rounded-xl border border-[#FFD2BA] bg-white text-xs font-bold text-[#B83D08] hover:bg-[#FFF5EC] transition cursor-pointer flex items-center space-x-1">
                            <span>💨</span>
                            <span>Breathing</span>
                        </button>
                    </div>
                </div>

                <!-- Focus Zone Card -->
                <div class="recovery-card-focuszone bg-white border border-[#EAE4DF] rounded-3xl p-5 space-y-4 shadow-xs flex flex-col justify-between">
                    <div class="space-y-3">
                        <div class="w-10 h-10 rounded-2xl bg-[#EDF7F1] text-[#166545] flex items-center justify-center text-lg font-bold shadow-xs">
                            🎯
                        </div>
                        <div>
                            <span class="text-[10px] font-extrabold uppercase tracking-wider text-[#166545]">
                                FOCUS ZONE
                            </span>
                            <h4 class="font-heading text-base font-extrabold text-[#202124] mt-0.5">
                                Want some quiet space to focus?
                            </h4>
                            <p class="text-xs text-[#6F6B68] leading-relaxed mt-1">
                                Start a Focus session at your own pace with intentional breaks.
                            </p>
                        </div>
                    </div>
                    <div class="pt-2">
                        <button onclick="if (window.TempoFocusZone) { window.TempoFocusZone.openQuickEntry(); } else if (window.TempoTriage) { window.TempoTriage.launchFocusMode(); }"
                                class="w-full py-2.5 px-4 rounded-xl bg-stone-100 hover:bg-stone-200 text-[#202124] font-bold text-xs transition text-center shadow-xs cursor-pointer">
                            Start Focus →
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    function renderRecentlyCard(recentlyState) {
        if (window.TempoSelfCheckHistory && typeof window.TempoSelfCheckHistory.renderRecentlyCard === 'function') {
            return window.TempoSelfCheckHistory.renderRecentlyCard();
        }

        if (recentlyState && recentlyState.type === 'NOT_ENOUGH') {
            return `
                <div class="recovery-card-recently bg-white border border-[#EAE4DF] rounded-3xl p-6 sm:p-7 space-y-4 shadow-xs flex flex-col justify-between h-full">
                    <div class="space-y-3">
                        <div class="flex items-center space-x-2">
                            <span class="text-[11px] font-extrabold uppercase tracking-wider text-[#6F6B68]">
                                RECENTLY
                            </span>
                        </div>
                        <h4 class="font-heading text-base sm:text-lg font-extrabold text-[#202124]">
                            You're just getting started.
                        </h4>
                        <p class="text-xs text-[#6F6B68] leading-relaxed">
                            There's not enough history to compare yet. Keep checking in at your own pace.
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
            <div class="recovery-card-recently bg-white border border-[#EAE4DF] rounded-3xl p-6 sm:p-7 space-y-4 shadow-xs flex flex-col justify-between h-full">
                <div class="space-y-3">
                    <div class="flex items-center space-x-2">
                        <span class="text-[11px] font-extrabold uppercase tracking-wider text-[#6F6B68]">
                            RECENTLY
                        </span>
                    </div>
                    <h4 class="font-heading text-base sm:text-lg font-extrabold text-[#202124]">
                        Nothing here yet.
                    </h4>
                    <p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed">
                        Once you start checking in, this space can help you look back at what you've been noticing over time.
                    </p>
                </div>
                <div class="pt-4 border-t border-stone-100 text-[11px] text-[#6F6B68]">
                    <span>Nothing needs to be recorded until you're ready.</span>
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
            <div class="recovery-card-weeklyreview bg-gradient-to-br from-[#F4FAF6] to-[#EDF7F1] border border-[#CDE9DA] rounded-3xl p-6 sm:p-7 space-y-4 shadow-xs">
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
            <div class="recovery-section-today space-y-3 pt-1">
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
            <div class="recovery-section-posts space-y-4 pt-2">
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
        renderShellIndicator,
        openChangeModeModal,
        closeChangeModeModal,
        toggleModeDropdown,
        toggleNavbarModeDropdown,
        closeAllModeDropdowns,
        selectModeFromDropdown,
        renderEmodeHome,
        renderRmodeHome,
        renderUmodeHome,
        restoreDefaultHome,
        renderActiveModeHome,
        applyModeVisibility,
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
        getSafeGreetingInfo
    };
})();

