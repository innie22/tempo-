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
            if (savedMode && Object.values(MODES).includes(savedMode)) {
                // If unauthenticated and savedMode is not default, normalize to default
                const isAuthenticated = window.TempoAuth && !!window.TempoAuth.getCurrentUser();
                if (savedMode !== MODES.DEFAULT && !isAuthenticated) {
                    currentMode = MODES.DEFAULT;
                    localStorage.setItem('tempo_current_mode', MODES.DEFAULT);
                } else {
                    currentMode = savedMode;
                }
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

        // If starting in emergency mode on the today screen, render Emode home
        if (currentMode === MODES.EMERGENCY) {
            renderEmodeHome();
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

        window.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && changeModeModal && !changeModeModal.classList.contains('hidden')) {
                closeChangeModeModal();
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
            case MODES.EMERGENCY: return 'Emergency Mode';
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
                if (window.TempoApp) window.TempoApp.navigateTo('emergency');
            } else if (targetMode === MODES.RECOVERY) {
                if (window.TempoApp) window.TempoApp.navigateTo('recovery-mode');
            } else if (targetMode === MODES.UNCLEAR) {
                if (window.TempoApp) window.TempoApp.navigateTo('unclear-mode');
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
                    window.TempoApp.navigateTo('emergency');
                    window.TempoApp.showToast("Welcome! Resuming your Emergency Mode setup.");
                }
            } else if (target === MODES.RECOVERY) {
                if (window.TempoApp) {
                    window.TempoApp.navigateTo('recovery-mode');
                    window.TempoApp.showToast("Welcome! Entering Recovery Mode.");
                }
            } else if (target === MODES.UNCLEAR) {
                if (window.TempoApp) {
                    window.TempoApp.navigateTo('unclear-mode');
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

        if (!options.silent && window.TempoApp) {
            if (newMode === MODES.EMERGENCY) {
                window.TempoApp.showToast("⚡ Emergency Mode active");
            } else if (newMode === MODES.RECOVERY) {
                window.TempoApp.showToast("🌱 Switched to Recovery Mode");
            } else if (newMode === MODES.UNCLEAR) {
                window.TempoApp.showToast("🧭 Switched to Unclear Mode");
            } else if (newMode === MODES.DEFAULT) {
                window.TempoApp.showToast("Returned to Default Tempo. All tasks remain saved.");
            }
        }

        // Synchronize view for current tab
        if (newMode === MODES.EMERGENCY) {
            renderEmodeHome();
            if (window.TempoApp && !options.silent) {
                window.TempoApp.navigateTo('emergency');
            }
        } else if (newMode === MODES.DEFAULT) {
            restoreDefaultHome();
        } else if (newMode === MODES.RECOVERY) {
            restoreDefaultHome();
            if (window.TempoApp) window.TempoApp.navigateTo('recovery-mode');
        } else if (newMode === MODES.UNCLEAR) {
            restoreDefaultHome();
            if (window.TempoApp) window.TempoApp.navigateTo('unclear-mode');
        }
    }

    // =========================================================================
    // GLOBAL SHELL INDICATOR & "CHANGE MODE" MODAL
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
            label.textContent = 'Emergency Mode';
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
    // DYNAMIC EMODE HOME STATE SYSTEM
    // =========================================================================

    function restoreDefaultHome() {
        const dmodeBox = document.getElementById('dmode-home-content');
        const emodeBox = document.getElementById('emode-home-content');
        if (dmodeBox) dmodeBox.classList.remove('hidden');
        if (emodeBox) emodeBox.classList.add('hidden');
    }

    function renderEmodeHome() {
        if (currentMode !== MODES.EMERGENCY) {
            restoreDefaultHome();
            return;
        }

        const dmodeBox = document.getElementById('dmode-home-content');
        const emodeBox = document.getElementById('emode-home-content');
        if (dmodeBox) dmodeBox.classList.add('hidden');
        if (!emodeBox) return;

        emodeBox.classList.remove('hidden');

        // Inspect shared emergency state from window.TempoEmergencyFlow
        const confirmedPlan = window.TempoEmergencyFlow && window.TempoEmergencyFlow.getConfirmedPlan
            ? window.TempoEmergencyFlow.getConfirmedPlan()
            : null;
        const currentStage = window.TempoEmergencyFlow && window.TempoEmergencyFlow.getCurrentStage
            ? window.TempoEmergencyFlow.getCurrentStage()
            : 'entry';
        const availabilityDays = window.TempoEmergencyFlow && window.TempoEmergencyFlow.getAvailabilityDays
            ? window.TempoEmergencyFlow.getAvailabilityDays()
            : [];

        const todayStr = getTodayISOString();
        const profile = window.TempoAuth ? window.TempoAuth.getCurrentProfile() : null;
        const greetingName = profile ? (window.TempoAuth.extractGreetingName(profile.full_name) || 'there') : 'there';

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
            ${renderEmodeHeader(greetingName)}
            ${renderStateBody(activeHomeState, { confirmedPlan, currentStage, availabilityDays, todayStr })}
        `;
    }

    function renderEmodeHeader(greetingName) {
        return `
            <div class="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-[#EAE4DF] gap-3">
                <div class="space-y-0.5">
                    <div class="flex items-center space-x-2">
                        <span class="px-2.5 py-0.5 rounded-full text-[11px] font-extrabold bg-[#FFE9DC] text-[#B83D08] uppercase tracking-wider flex items-center space-x-1 shadow-xs">
                            <span>⚡</span>
                            <span>Emergency Mode</span>
                        </span>
                        <span class="text-xs text-[#6F6B68] font-medium">• Academic Deadline Triage</span>
                    </div>
                    <h2 class="font-heading text-2xl sm:text-3xl font-extrabold text-[#202124] tracking-tight">
                        Hi, ${escapeHTML(greetingName)} 👋 Take it one doable step at a time.
                    </h2>
                </div>
                <div class="flex items-center space-x-2 shrink-0">
                    <button onclick="window.TempoMode.openChangeModeModal()" class="px-3.5 py-2 rounded-xl border border-gray-200 text-xs font-semibold text-gray-700 bg-white hover:bg-stone-50 transition shadow-xs">
                        Change mode
                    </button>
                    <button onclick="window.TempoApp.navigateTo('emergency')" class="btn-primary px-4 py-2 rounded-xl text-xs font-bold shadow-sm transition">
                        Open Setup Flow →
                    </button>
                </div>
            </div>
        `;
    }

    function renderStateBody(state, ctx) {
        const { confirmedPlan, currentStage, availabilityDays, todayStr } = ctx;

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
                return renderStateActiveToday(confirmedPlan, todayStr);
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
            'plan-review': 'Emergency Plan Review & Schedule',
            'breakdown': 'Step Breakdown',
            'handoff': 'Start Working Handoff'
        };

        const currentStageTitle = stageNames[currentStage] || 'Emergency Setup';

        return `
            <div class="space-y-8">
                <!-- Resume Card -->
                <div class="bg-white border-2 border-dashed border-[#FF6B2C]/50 rounded-3xl p-6 sm:p-8 space-y-5 shadow-xs">
                    <div class="space-y-2">
                        <span class="px-3 py-1 rounded-full text-[11px] font-extrabold bg-[#FFE9DC] text-[#B83D08] uppercase tracking-wider">
                            YOUR EMERGENCY PLAN
                        </span>
                        <h3 class="font-heading text-xl sm:text-2xl font-extrabold text-[#202124]">
                            You're still setting up your plan.
                        </h3>
                        <p class="text-xs sm:text-sm text-[#6F6B68] max-w-lg leading-relaxed">
                            Your emergency plan setup is in progress at step: <strong class="text-[#202124]">${currentStageTitle}</strong>.
                            All of your task entries and estimates are safely preserved.
                        </p>
                    </div>

                    <div class="pt-2 flex flex-wrap items-center gap-3">
                        <button onclick="window.TempoApp.navigateTo('emergency'); window.TempoEmergencyFlow.goToStage('${currentStage}');"
                                class="btn-primary px-6 py-3 rounded-xl font-bold text-xs sm:text-sm shadow-md inline-flex items-center space-x-2 transition">
                            <span>Continue building my plan</span>
                            <span>→</span>
                        </button>
                        <button onclick="window.TempoMode.openChangeModeModal()" 
                                class="px-4 py-3 rounded-xl border border-gray-200 text-xs font-semibold text-gray-700 bg-white hover:bg-stone-50 transition">
                            Switch mode
                        </button>
                    </div>
                </div>

                <!-- Quick Tools stay accessible -->
                ${renderQuickToolsSection('active')}
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
                            Your Emergency Plan is complete.
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
                                class="btn-primary px-6 py-3 rounded-xl font-bold text-xs sm:text-sm shadow-md transition">
                            Shift to Recovery Mode →
                        </button>
                        <button onclick="window.TempoMode.openChangeModeModal()" 
                                class="px-5 py-3 rounded-xl border border-gray-200 text-xs font-semibold text-gray-700 bg-white hover:bg-stone-50 transition">
                            Change mode
                        </button>
                        <button onclick="window.TempoApp.showToast('Remaining in Emergency Mode.')" 
                                class="px-4 py-3 text-xs text-[#6F6B68] hover:text-[#202124] underline">
                            Stay in Emergency Mode
                        </button>
                    </div>
                </div>

                ${renderQuickToolsSection('recovery')}
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
                                <span class="text-stone-500 text-[11px]">Was scheduled: ${t.dayLabel}</span>
                            </div>
                        `).join('')}
                    </div>

                    <div class="pt-2 flex flex-wrap items-center gap-3">
                        <button onclick="window.TempoApp.navigateTo('emergency'); window.TempoEmergencyFlow.goToStage('plan-review');"
                                class="btn-primary px-5 py-2.5 rounded-xl font-bold text-xs shadow-sm transition">
                            Review & update plan →
                        </button>
                        <button onclick="window.TempoMode.dismissStaleWarning()" 
                                class="px-4 py-2.5 rounded-xl border border-amber-300 text-xs font-semibold text-amber-900 bg-white hover:bg-amber-100/50 transition">
                            Dismiss for now
                        </button>
                    </div>
                </div>

                ${renderQuickToolsSection('active')}
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
                                    class="px-5 py-2.5 rounded-xl bg-stone-100 hover:bg-stone-200 text-stone-800 text-xs font-bold transition">
                                Stop for today
                            </button>
                            <button onclick="window.TempoMode.keepWorkingToday()" 
                                    class="btn-primary px-5 py-2.5 rounded-xl text-xs font-bold shadow-sm transition">
                                Keep working
                            </button>
                            <button onclick="window.TempoApp.navigateTo('emergency'); window.TempoEmergencyFlow.goToStage('plan-review');" 
                                    class="px-4 py-2.5 rounded-xl border border-gray-200 text-xs font-semibold text-gray-700 bg-white hover:bg-stone-50 transition">
                                Adjust my plan
                            </button>
                        </div>
                    </div>
                </div>

                ${renderQuickToolsSection('active')}
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
                            <button onclick="window.TempoApp.navigateTo('emergency'); window.TempoEmergencyFlow.goToStage('plan-review');"
                                    class="px-4 py-2 rounded-xl border border-gray-200 bg-white font-semibold text-xs text-gray-700 hover:bg-stone-50 transition self-start sm:self-auto">
                                View tomorrow →
                            </button>
                        ` : ''}
                    </div>
                </div>

                <!-- After work is complete: Quick Tools prioritize stress relief & breathing -->
                ${renderQuickToolsSection('recovery')}
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
                            Your Emergency Plan continues on <strong>${escapeHTML(nextDateLabel)}</strong>.
                        </p>
                    </div>

                    <div class="pt-2 flex items-center space-x-3">
                        <button onclick="window.TempoApp.navigateTo('emergency'); window.TempoEmergencyFlow.goToStage('plan-review');"
                                class="px-4 py-2.5 rounded-xl border border-gray-200 text-xs font-semibold text-gray-700 hover:bg-stone-50 transition">
                            View Plan Schedule →
                        </button>
                    </div>
                </div>

                ${renderQuickToolsSection('active')}
            </div>
        `;
    }

    // -------------------------------------------------------------------------
    // STATE B: ACTIVE_TODAY (Core Execution View)
    // -------------------------------------------------------------------------
    function renderStateActiveToday(confirmedPlan, todayStr) {
        const allPlanned = confirmedPlan.plannedTasks || [];
        const todayTasks = allPlanned.filter(pt => pt.dayDate === todayStr);

        // Final plan execution order: find first uncompleted task for today
        const upNextItem = todayTasks.find(pt => !pt.task.completed) || todayTasks[0];
        const completedCount = todayTasks.filter(pt => pt.task.completed).length;

        // Determine next concrete action text from subtasks
        let nextActionText = "Begin focused preliminary work block.";
        if (upNextItem && upNextItem.task.subtasks && upNextItem.task.subtasks.length > 0) {
            const firstIncompleteSubtask = upNextItem.task.subtasks.find(s => !s.completed);
            nextActionText = firstIncompleteSubtask ? firstIncompleteSubtask.title : upNextItem.task.subtasks[0].title;
        }

        // Check for "Needs Attention" items (ONLY if actual issues exist!)
        const needsAttentionItems = checkNeedsAttentionIssues(confirmedPlan, todayStr);

        return `
            <div class="space-y-8">
                <!-- 1. UP NEXT / CONTINUE SECTION (Primary Hero) -->
                ${upNextItem ? `
                    <div class="bg-white border-2 border-[#FF6B2C] rounded-3xl p-6 sm:p-7 space-y-4 shadow-sm">
                        <div class="flex items-center justify-between pb-2 border-b border-gray-100">
                            <div class="flex items-center space-x-2">
                                <span class="px-3 py-1 rounded-full text-xs font-extrabold bg-[#FFE9DC] text-[#B83D08] uppercase tracking-wider">
                                    ${upNextItem.task.isInProgress ? '⚡ CONTINUE' : '✨ UP NEXT'}
                                </span>
                                <span class="text-xs text-[#6F6B68] font-medium">• Planned for today</span>
                            </div>
                            <span class="text-xs font-bold text-[#FF6B2C]">
                                ${upNextItem.startTime && upNextItem.endTime ? `${upNextItem.startTime} – ${upNextItem.endTime}` : (upNextItem.task.isUnknownDuration ? 'Time not estimated' : `~${upNextItem.task.durationLabel}`)}
                            </span>
                        </div>

                        <div class="space-y-2">
                            <div class="flex items-baseline justify-between gap-3">
                                <h3 class="font-heading text-xl sm:text-2xl font-bold text-[#202124]">
                                    ${escapeHTML(upNextItem.task.name)}
                                </h3>
                                <span class="text-xs font-semibold ${upNextItem.hasDeadlineConflict ? 'text-rose-600 font-bold' : 'text-[#6F6B68]'} shrink-0">
                                    ${upNextItem.task.hasDeadline ? `Due: ${formatHumanDeadline(upNextItem.task.deadlineDate, upNextItem.task.deadlineTime)}` : 'No fixed deadline'}
                                </span>
                            </div>

                            <!-- Next Concrete Action Callout -->
                            <div class="p-3.5 bg-[#FFF8F2] border border-[#FFD2BA] rounded-2xl space-y-1">
                                <span class="text-[11px] font-bold uppercase tracking-wider text-[#B83D08]">Next Concrete Action:</span>
                                <p class="text-xs font-semibold text-[#202124]">${escapeHTML(nextActionText)}</p>
                            </div>
                        </div>

                        <!-- Action Buttons -->
                        <div class="pt-2 flex flex-wrap items-center justify-between gap-3 border-t border-gray-100">
                            <div class="flex items-center space-x-2">
                                <button onclick="window.TempoMode.startTaskFocus('${upNextItem.task.id}')"
                                        class="btn-primary px-6 py-2.5 rounded-xl font-bold text-xs sm:text-sm shadow-sm inline-flex items-center space-x-2 transition">
                                    <span>${upNextItem.task.isInProgress ? 'Continue Focus' : 'Do now'}</span>
                                    <span>→</span>
                                </button>
                                <button onclick="window.TempoApp.navigateTo('emergency'); window.TempoEmergencyFlow.goToStage('breakdown');"
                                        class="px-4 py-2.5 rounded-xl border border-gray-200 text-xs font-semibold text-gray-700 bg-white hover:bg-stone-50 transition">
                                    View task & breakdown
                                </button>
                            </div>
                            <button onclick="window.TempoMode.toggleTaskCompletion('${upNextItem.task.id}')"
                                    class="px-3.5 py-2 rounded-xl text-xs font-bold text-emerald-800 bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 transition flex items-center space-x-1">
                                <span>✓</span>
                                <span>Mark complete</span>
                            </button>
                        </div>
                    </div>
                ` : ''}

                <!-- 2. TODAY'S PLANNED TASKS (Factual progress, execution order) -->
                <div class="bg-white border border-[#EAE4DF] rounded-3xl p-6 sm:p-7 space-y-4 shadow-xs">
                    <div class="flex items-center justify-between pb-2 border-b border-gray-100">
                        <div>
                            <h4 class="font-heading text-base font-bold text-[#202124]">Today's Planned Tasks</h4>
                            <p class="text-xs text-[#6F6B68]">In confirmed execution order</p>
                        </div>
                        <span class="px-3 py-1 rounded-full text-xs font-bold bg-stone-100 text-stone-700">
                            ${completedCount} of ${todayTasks.length} done
                        </span>
                    </div>

                    <div class="space-y-2.5">
                        ${todayTasks.map((item, idx) => {
                            const isDone = item.task.completed === true;
                            const isCurrent = upNextItem && item.task.id === upNextItem.task.id && !isDone;

                            return `
                                <div class="p-3.5 rounded-2xl border transition flex items-center justify-between gap-3 ${isDone ? 'bg-stone-50 border-stone-200 opacity-60' : (isCurrent ? 'bg-[#FFF9F4] border-[#FF6B2C]/50 shadow-xs' : 'bg-white border-[#EAE4DF]')}">
                                    <div class="flex items-center space-x-3 min-w-0 flex-1">
                                        <button onclick="window.TempoMode.toggleTaskCompletion('${item.task.id}')"
                                                class="w-6 h-6 rounded-lg border flex items-center justify-center text-xs font-bold transition shrink-0 ${isDone ? 'bg-emerald-600 border-emerald-600 text-white' : 'border-stone-300 hover:border-[#FF6B2C] bg-white text-transparent'}">
                                            ✓
                                        </button>
                                        <div class="min-w-0 flex-1">
                                            <div class="flex items-center space-x-2">
                                                <h5 class="text-xs font-bold ${isDone ? 'line-through text-stone-500' : 'text-[#202124]'} truncate">
                                                    ${escapeHTML(item.task.name)}
                                                </h5>
                                                ${isCurrent ? `
                                                    <span class="px-2 py-0.2 rounded text-[9px] font-extrabold bg-[#FFE9DC] text-[#B83D08] uppercase shrink-0">
                                                        NEXT
                                                    </span>
                                                ` : ''}
                                            </div>
                                            <p class="text-[11px] text-[#6F6B68]">
                                                ${item.task.isUnknownDuration ? 'Time not estimated' : `~${item.task.durationLabel}`}
                                                ${item.task.hasDeadline ? `• Due ${item.task.deadlineDate} ${item.task.deadlineTime || ''}` : ''}
                                            </p>
                                        </div>
                                    </div>
                                    <div class="flex items-center space-x-2 shrink-0">
                                        <span class="px-2 py-0.5 rounded text-[10px] font-bold ${item.executionBadge === 'UP NEXT' ? 'bg-[#FFE9DC] text-[#B83D08]' : 'bg-stone-100 text-stone-600'}">
                                            ${item.executionBadge || 'THEN'}
                                        </span>
                                    </div>
                                </div>
                            `;
                        }).join('')}
                    </div>
                </div>

                <!-- 3. QUICK TOOLS -->
                ${renderQuickToolsSection('active')}

                <!-- 4. EMERGENCY PLAN SUMMARY -->
                <div class="p-5 bg-white border border-[#EAE4DF] rounded-3xl flex flex-col sm:flex-row sm:items-center justify-between gap-4 text-xs shadow-xs">
                    <div class="space-y-0.5">
                        <h5 class="font-bold text-[#202124]">Emergency Plan Overview</h5>
                        <p class="text-[#6F6B68]">
                            Total planned: ${allPlanned.length} task${allPlanned.length === 1 ? '' : 's'} across ${(confirmedPlan.totalWorkloadMinutes ? Math.round(confirmedPlan.totalWorkloadMinutes / 60) : 0)} hours planned workload.
                        </p>
                    </div>
                    <div class="flex items-center space-x-2">
                        <button onclick="window.TempoApp.navigateTo('emergency'); window.TempoEmergencyFlow.goToStage('plan-review');"
                                class="px-4 py-2 rounded-xl border border-gray-200 text-xs font-semibold text-gray-700 bg-white hover:bg-stone-50 transition">
                            View / Edit Full Plan →
                        </button>
                    </div>
                </div>

                <!-- 5. NEEDS ATTENTION (ONLY WHEN ACTUAL ISSUES EXIST) -->
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
                                    <button onclick="window.TempoApp.navigateTo('emergency'); window.TempoEmergencyFlow.goToStage('plan-review');"
                                            class="px-3 py-1.5 bg-amber-200 hover:bg-amber-300 text-amber-950 font-bold rounded-lg text-[11px] shrink-0 self-start sm:self-auto transition">
                                        Review Plan
                                    </button>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}
            </div>
        `;
    }

    // -------------------------------------------------------------------------
    // QUICK TOOLS RENDERER (Adaptive Ordering)
    // -------------------------------------------------------------------------
    function renderQuickToolsSection(modeContext = 'active') {
        // Active work order: Focus Zone, Quick Stress Relief, Breathing, Self-check
        // Post-work / recovery order: Quick Stress Relief, Breathing, Focus Zone, Self-check
        const tools = [
            {
                id: 'focus',
                name: 'Focus Zone',
                desc: 'Focus with intentional breaks. Default 45m focus / 15m rest.',
                icon: '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>',
                action: "if (window.TempoFocusZone) { window.TempoFocusZone.openQuickEntry(); } else if (window.TempoTriage) { window.TempoTriage.launchFocusMode(); }"
            },
            {
                id: 'stress',
                name: 'Quick Stress Relief',
                desc: 'Simple micro-actions to ease acute tension in a few minutes.',
                icon: '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>',
                action: "window.TempoStressRelief.openModal()"
            },
            {
                id: 'breathing',
                name: 'Breathing',
                desc: 'A quick breathing exercise to calm your heart rate.',
                icon: '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"/></svg>',
                action: "window.TempoTriage.openBoxBreathingModal()"
            },
            {
                id: 'check',
                name: 'Self-check',
                desc: 'Track stress signals and non-judgmental habits.',
                icon: '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/></svg>',
                action: "window.TempoApp.navigateTo('stress-check')"
            }
        ];

        let orderedTools = tools;
        if (modeContext === 'recovery') {
            orderedTools = [tools[1], tools[2], tools[0], tools[3]];
        }

        return `
            <div class="space-y-4 pt-2">
                <div class="flex items-center justify-between">
                    <div>
                        <h4 class="font-heading text-lg sm:text-xl font-extrabold text-[#202124]">Quick Tools</h4>
                        <p class="text-xs text-[#6F6B68]">Calming utilities and regulation support</p>
                    </div>
                </div>

                <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    ${orderedTools.map(tool => `
                        <div onclick="${tool.action}" class="quick-tool-card p-5 cursor-pointer flex flex-col justify-between space-y-4 group">
                            <div class="space-y-3">
                                <div class="quick-tool-icon-circle">
                                    ${tool.icon}
                                </div>
                                <div>
                                    <h5 class="font-heading text-sm font-bold text-[#202124] group-hover:text-[#FF6B2C] transition">${tool.name}</h5>
                                    <p class="text-xs text-[#6F6B68] leading-relaxed mt-1">${tool.desc}</p>
                                </div>
                            </div>
                            <div class="flex justify-end pt-1">
                                <div class="quick-tool-arrow-btn">→</div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    // =========================================================================
    // TASK & PLAN INTERACTIONS
    // =========================================================================

    function toggleTaskCompletion(taskId) {
        if (!window.TempoEmergencyFlow || !window.TempoEmergencyFlow.toggleTaskCompleted) return;

        const isNowCompleted = window.TempoEmergencyFlow.toggleTaskCompleted(taskId);

        if (isNowCompleted && window.TempoApp) {
            window.TempoApp.triggerConfetti();
            window.TempoApp.showToast("Task completed! Taking small steps protects your momentum.");
        }

        renderEmodeHome();
    }

    function startTaskFocus(taskId) {
        if (window.TempoEmergencyFlow && window.TempoEmergencyFlow.setTaskInProgress) {
            window.TempoEmergencyFlow.setTaskInProgress(taskId, true);
        }

        if (window.TempoFocusZone && window.TempoFocusZone.open) {
            window.TempoFocusZone.open({ taskId: taskId });
        } else if (window.TempoTriage) {
            window.TempoTriage.launchFocusMode();
            const confirmedPlan = window.TempoEmergencyFlow ? window.TempoEmergencyFlow.getConfirmedPlan() : null;
            const taskItem = confirmedPlan?.plannedTasks?.find(pt => pt.task.id === taskId);
            if (taskItem && taskItem.task && taskItem.task.name) {
                const taskNameEl = document.getElementById('focus-task-name');
                if (taskNameEl) {
                    taskNameEl.textContent = taskItem.task.name;
                }
            }
        }
        renderEmodeHome();
    }

    function stopForToday() {
        sessionFlags.dismissedTimeEndedToday = true;
        if (window.TempoApp) {
            window.TempoApp.showToast("Stopped for today. Rest and recovery are essential for tomorrow's focus.");
        }
        renderEmodeHome();
    }

    function keepWorkingToday() {
        sessionFlags.dismissedTimeEndedToday = true;
        if (window.TempoApp) {
            window.TempoApp.showToast("Continuing work today.");
        }
        renderEmodeHome();
    }

    function dismissStaleWarning() {
        sessionFlags.dismissedStaleWarning = true;
        renderEmodeHome();
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
        getPendingMode,
        hasPendingMode,
        getModeDisplayName,
        requestMode,
        handleAuthSuccess,
        setMode,
        renderShellIndicator,
        openChangeModeModal,
        closeChangeModeModal,
        renderEmodeHome,
        toggleTaskCompletion,
        startTaskFocus,
        stopForToday,
        keepWorkingToday,
        dismissStaleWarning
    };
})();
