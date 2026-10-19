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

    // Source context for shared assessment / tools: 'entry' | 'emergency' | 'recovery'
    let sourceContext = 'entry';

    // Central pending intent across auth gate: null | { type: 'mode'|'tool', destination: string, tool?: string, sourceContext?: string }
    let pendingIntent = null;

    // Session-level flags to prevent repeating dismissed alerts
    let sessionFlags = {
        dismissedStaleWarning: false,
        dismissedTimeEndedToday: false,
        viewingTomorrowTask: false,
        restingForToday: false
    };

    let currentActiveHomeState = null;

    // Expanded task cards on Default Home
    let dmodeExpandedTaskIds = new Set();

    function hasEstablishedContext() {
        try {
            const uid = window.TempoAuth && typeof window.TempoAuth.getCurrentUserId === 'function' ? window.TempoAuth.getCurrentUserId() : null;
            if (uid) {
                const userSaved = localStorage.getItem('tempo_user_established_context_' + uid);
                if (userSaved === MODES.EMERGENCY || userSaved === MODES.RECOVERY) return true;
                if (userSaved === MODES.DEFAULT) return false;
            }

            const savedEstablished = localStorage.getItem('tempo_established_context');
            if (savedEstablished === MODES.EMERGENCY || savedEstablished === MODES.RECOVERY) return true;
            if (savedEstablished === MODES.DEFAULT) return false;

            const savedMode = localStorage.getItem('tempo_current_mode');
            if (savedMode === MODES.EMERGENCY || savedMode === MODES.RECOVERY) return true;
        } catch (e) {}

        return false;
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

            if (authState === 'AUTH_LOADING') {
                if (savedMode === MODES.EMERGENCY || savedMode === MODES.RECOVERY) {
                    activeContext = savedMode;
                    sourceContext = savedMode;
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
                const established = userEstablished;
                if (established === MODES.EMERGENCY) {
                    activeContext = MODES.EMERGENCY;
                    sourceContext = 'emergency';
                } else if (established === MODES.RECOVERY) {
                    activeContext = MODES.RECOVERY;
                    sourceContext = 'recovery';
                } else {
                    // Authenticated user with no established active context -> Entry Home
                    activeContext = null;
                    sourceContext = 'entry';
                    localStorage.setItem('tempo_current_mode', MODES.DEFAULT);
                }
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

    function getSourceContext() {
        return sourceContext;
    }

    function setSourceContext(ctx) {
        if (ctx === 'emergency' || ctx === 'recovery' || ctx === 'entry') {
            sourceContext = ctx;
        } else {
            sourceContext = 'entry';
        }
    }

    function getActiveSharedTool() {
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

    function getMode() {
        if (activeSharedTool === 'ucheck') return MODES.UNCLEAR;
        if (activeContext === MODES.EMERGENCY) return MODES.EMERGENCY;
        if (activeContext === MODES.RECOVERY) return MODES.RECOVERY;
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
        if (targetContext !== MODES.EMERGENCY && targetContext !== MODES.RECOVERY) {
            targetContext = null;
        }

        const prevContext = activeContext;
        activeContext = targetContext;
        activeSharedTool = null;

        // Establish sourceContext according to new activeContext
        sourceContext = targetContext === MODES.EMERGENCY ? 'emergency' : (targetContext === MODES.RECOVERY ? 'recovery' : 'entry');

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
                if (uid) {
                    localStorage.setItem('tempo_user_established_context_' + uid, MODES.DEFAULT);
                }
            }
        } catch (e) {}

        renderShellIndicator();
        closeChangeModeModal();
        closeAllModeDropdowns();

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
            if (!options.skipSetupCheck && window.TempoRecoverySetup && typeof window.TempoRecoverySetup.shouldShowFirstTimeWelcome === 'function') {
                if (window.TempoRecoverySetup.shouldShowFirstTimeWelcome()) {
                    window.TempoRecoverySetup.open(1);
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
        const src = options.sourceContext || (activeContext === MODES.EMERGENCY ? 'emergency' : (activeContext === MODES.RECOVERY ? 'recovery' : 'entry'));
        sourceContext = src;

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

        let src;
        if (options && options.sourceContext) {
            src = options.sourceContext;
        } else if (activeContext === MODES.RECOVERY) {
            src = 'recovery';
        } else if (activeContext === MODES.EMERGENCY) {
            src = 'emergency';
        } else {
            src = sourceContext || 'entry';
        }
        sourceContext = src;

        const returnLabelEl = document.getElementById('stress-check-return-text');
        if (returnLabelEl) {
            if (src === 'recovery') returnLabelEl.textContent = 'Return to Recovery Mode';
            else if (src === 'emergency') returnLabelEl.textContent = 'Return to Urgent Mode';
            else returnLabelEl.textContent = 'Return';
        }

        const isAuthenticated = Boolean(
            window.TempoAuth && 
            typeof window.TempoAuth.getCurrentUser === 'function' && 
            window.TempoAuth.getCurrentUser() &&
            (typeof window.TempoAuth.getAuthState !== 'function' || window.TempoAuth.getAuthState() === 'authenticated') &&
            !(typeof window.TempoAuth.isRegistrationInProgress === 'function' && window.TempoAuth.isRegistrationInProgress())
        );

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
        const isAuthenticated = Boolean(
            window.TempoAuth && 
            typeof window.TempoAuth.getCurrentUser === 'function' && 
            window.TempoAuth.getCurrentUser() &&
            (typeof window.TempoAuth.getAuthState !== 'function' || window.TempoAuth.getAuthState() === 'authenticated') &&
            !(typeof window.TempoAuth.isRegistrationInProgress === 'function' && window.TempoAuth.isRegistrationInProgress())
        );

        if (!isAuthenticated) {
            console.warn("[TempoMode] Protected route access blocked: Strack requires authentication.");
            openStrack('open');
            return;
        }

        document.querySelectorAll('.screen-container').forEach(screen => {
            screen.classList.add('hidden');
        });
        const target = document.getElementById('screen-stress-check');
        if (target) {
            target.classList.remove('hidden');
        }
        window.location.hash = '#stress-check';
        if (window.TempoApp && typeof window.TempoApp.updateNavActiveState === 'function') {
            window.TempoApp.updateNavActiveState('stress-check');
        }
    }

    function executeStrackAction(action = 'open', options = {}) {
        const isAuthenticated = Boolean(
            window.TempoAuth && 
            typeof window.TempoAuth.getCurrentUser === 'function' && 
            window.TempoAuth.getCurrentUser() &&
            (typeof window.TempoAuth.getAuthState !== 'function' || window.TempoAuth.getAuthState() === 'authenticated') &&
            !(typeof window.TempoAuth.isRegistrationInProgress === 'function' && window.TempoAuth.isRegistrationInProgress())
        );

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
        } else if (action === 'manage') {
            if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.openManage === 'function') {
                window.TempoRecoverySelfCheck.openManage();
            } else {
                showStressCheckScreen();
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
            // General open action
            if (activeContext === MODES.RECOVERY) {
                const scState = getSelfCheckState();
                if (scState && scState.type === 'STATE_A') {
                    if (window.TempoRecoverySetup && typeof window.TempoRecoverySetup.open === 'function') {
                        window.TempoRecoverySetup.open(1);
                    } else if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.openSetup === 'function') {
                        window.TempoRecoverySelfCheck.openSetup();
                    } else {
                        showStressCheckScreen();
                    }
                } else {
                    if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.openDailyCheckin === 'function') {
                        window.TempoRecoverySelfCheck.openDailyCheckin(false);
                    } else {
                        showStressCheckScreen();
                    }
                }
            } else {
                // Outside Recovery Mode (Entry Home or Urgent Mode)
                showStressCheckScreen();
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
        activeSharedTool = null;

        // Close any open Strack modals
        if (window.TempoRecoverySelfCheck) {
            if (typeof window.TempoRecoverySelfCheck.closeManage === 'function') window.TempoRecoverySelfCheck.closeManage();
            if (typeof window.TempoRecoverySelfCheck.closeDailyCheckin === 'function') window.TempoRecoverySelfCheck.closeDailyCheckin();
            if (typeof window.TempoRecoverySelfCheck.closeTrackerModal === 'function') window.TempoRecoverySelfCheck.closeTrackerModal();
            if (typeof window.TempoRecoverySelfCheck.closeViewToday === 'function') window.TempoRecoverySelfCheck.closeViewToday();
        }
        if (window.TempoRecoverySetup && typeof window.TempoRecoverySetup.close === 'function') {
            window.TempoRecoverySetup.close();
        }

        const isAuthenticated = window.TempoAuth && typeof window.TempoAuth.getCurrentUser === 'function' && !!window.TempoAuth.getCurrentUser();
        if (!isAuthenticated) {
            activeContext = null;
            sourceContext = 'entry';
            renderShellIndicator();
            renderActiveModeHome();
            if (window.TempoApp) window.TempoApp.navigateTo('today');
            return;
        }

        const src = sourceContext || (activeContext === MODES.EMERGENCY ? 'emergency' : (activeContext === MODES.RECOVERY ? 'recovery' : 'entry'));

        if (src === 'emergency') {
            activeContext = MODES.EMERGENCY;
            sourceContext = 'emergency';
        } else if (src === 'recovery') {
            activeContext = MODES.RECOVERY;
            sourceContext = 'recovery';
        } else {
            activeContext = null;
            sourceContext = 'entry';
        }
        renderShellIndicator();
        renderActiveModeHome();
        if (window.TempoApp) window.TempoApp.navigateTo('today');
    }

    /**
     * Legacy adapter for requestMode.
     */
    function requestMode(targetMode) {
        if (targetMode === MODES.UNCLEAR) {
            openUcheck({ sourceContext: activeContext === MODES.EMERGENCY ? 'emergency' : (activeContext === MODES.RECOVERY ? 'recovery' : 'entry') });
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

            if (origin === 'emergency') {
                activeContext = MODES.EMERGENCY;
                sourceContext = 'emergency';
                renderActiveModeHome();
            } else if (origin === 'recovery') {
                activeContext = MODES.RECOVERY;
                sourceContext = 'recovery';
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
        let established = null;
        try {
            if (uid) {
                established = localStorage.getItem('tempo_user_established_context_' + uid);
            }
        } catch (e) {}

        const currentActive = activeContext;
        const intentSource = intent ? (intent.source || intent.sourceContext) : null;
        const dest = intent ? (intent.destination || intent.tool || '').toLowerCase() : '';
        const isToolOrAssessment = intent && (
            dest === 'strack' || dest === 'stress-check' ||
            intent.type === 'ucheck' || dest === 'ucheck' || dest === 'unclear' || dest === 'unclear-mode' ||
            dest === 'plan-workspace' || intent.type === 'tool'
        );

        let resolvedContext = null;
        if (established === MODES.EMERGENCY || established === MODES.RECOVERY) {
            resolvedContext = established;
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
                const savedSource = intent.source || intent.sourceContext || (activeContext === MODES.EMERGENCY ? 'emergency' : (activeContext === MODES.RECOVERY ? 'recovery' : 'entry'));
                sourceContext = savedSource;
                openUcheck(Object.assign({}, intent.requiredParams || intent.options || {}, { sourceContext: savedSource }));
                if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                    window.TempoApp.showToast("Signed in. Resuming Unclear Mode assessment.");
                }
                return true;
            } else if (isStrack) {
                // Resume Strack (Self-check) without changing activeContext
                const savedSource = intent.source || intent.sourceContext || (activeContext === MODES.RECOVERY ? 'recovery' : (activeContext === MODES.EMERGENCY ? 'emergency' : 'entry'));
                sourceContext = savedSource;
                openStrack(intent.action || 'open', intent.requiredParams || intent.options || {});
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
            openUcheck({ sourceContext: activeContext === MODES.EMERGENCY ? 'emergency' : (activeContext === MODES.RECOVERY ? 'recovery' : 'entry') });
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
        const shell = document.getElementById('mode-indicator-shell');
        const badge = document.getElementById('mode-badge') || document.getElementById('btn-mode-indicator-trigger');
        const icon = document.getElementById('mode-badge-icon');
        const label = document.getElementById('mode-badge-label');

        if (!shell || !badge || !icon || !label) return;

        const curMode = getMode();
        if (curMode === MODES.DEFAULT || curMode === MODES.EMERGENCY) {
            shell.classList.add('hidden');
            shell.classList.remove('flex');
            if (curMode === MODES.EMERGENCY) {
                icon.textContent = '⚡';
                label.textContent = window.t ? window.t('modes.urgent.name', {}, 'Urgent Mode') : 'Urgent Mode';
            }
            return;
        }

        shell.classList.remove('hidden');
        shell.classList.add('flex');

        if (curMode === MODES.RECOVERY) {
            badge.className = 'px-2.5 py-1 rounded-full text-xs font-bold bg-[#EDF7F1] text-[#166545] flex items-center space-x-1.5 shadow-sm';
            icon.textContent = '🌱';
            label.textContent = window.t ? window.t('modes.recovery.name', {}, 'Recovery Mode') : 'Recovery Mode';
        } else if (curMode === MODES.UNCLEAR) {
            badge.className = 'px-2.5 py-1 rounded-full text-xs font-bold bg-[#FEF7EC] text-[#9A5B13] flex items-center space-x-1.5 shadow-sm';
            icon.textContent = '🧭';
            label.textContent = window.t ? window.t('modes.unclear.name', {}, 'Unclear Mode') : 'Unclear Mode';
        }
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
        } else {
            document.body.style.backgroundColor = '';
            if (mainEl) mainEl.style.backgroundColor = '';
        }

        syncModeSelectorDOM(mode);
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

    function renderQuickReliefCardHTML(extraClass = '') {
        const widthClass = extraClass ? ` ${extraClass}` : '';
        return `
            <div onclick="if (window.TempoStressRelief && window.TempoStressRelief.openModal) { window.TempoStressRelief.openModal(); } else if (window.TempoTriage && window.TempoTriage.openQuickReliefModal) { window.TempoTriage.openQuickReliefModal(); }"
                 class="bg-[#E6EDE7] border border-[#736F68] rounded-3xl overflow-hidden p-4 sm:p-5 flex items-center justify-between min-h-[175px] h-[175px]${widthClass} shadow-[0_4px_10px_-2px_rgba(75,55,40,0.07),0_14px_28px_-5px_rgba(75,55,40,0.12)] hover:shadow-[0_6px_14px_-2px_rgba(75,55,40,0.09),0_20px_36px_-4px_rgba(75,55,40,0.16)] transition cursor-pointer group"
                 title="Quick Relief">
                <div class="flex-1 min-w-0 pr-1.5">
                    <h3 class="text-[22px] sm:text-[25px] font-bold text-[#92A491] mb-1 group-hover:text-[#7D8F7C] transition leading-tight whitespace-nowrap">
                        Quick Relief
                    </h3>
                    <p class="text-[14px] sm:text-[16px] text-[#92A491] leading-[1.35]">
                        <span class="sr-only">Feeling overwhelmed? </span>Quick ways to ease stress and feel better.
                    </p>
                </div>
                <img src="assets/quick-relief-mascot-transparent.png"
                     alt="Quick Relief Mascot"
                     class="w-[150px] h-[150px] object-contain shrink-0 select-none pointer-events-none" />
            </div>
        `;
    }

    function renderFocusNowCardHTML(extraClass = '') {
        const widthClass = extraClass ? ` ${extraClass}` : '';
        return `
            <div onclick="if (window.TempoFocusZone && window.TempoFocusZone.openQuickEntry) { window.TempoFocusZone.openQuickEntry(); } else if (window.TempoTriage && window.TempoTriage.launchFocusMode) { window.TempoTriage.launchFocusMode(); }"
                 class="bg-[#D7A690] border border-[#000000] rounded-3xl overflow-hidden p-4 sm:p-5 flex items-center justify-between min-h-[175px] h-[175px]${widthClass} shadow-[0_4px_10px_-2px_rgba(75,55,40,0.07),0_14px_28px_-5px_rgba(75,55,40,0.12)] hover:shadow-[0_6px_14px_-2px_rgba(75,55,40,0.09),0_20px_36px_-4px_rgba(75,55,40,0.16)] transition cursor-pointer group"
                 title="Focus Now">
                <img src="assets/focus-now-mascot.png"
                     alt="Focus Now Mascot"
                     class="w-[170px] h-[170px] -translate-x-[33px] -mr-[10px] object-contain shrink-0 select-none pointer-events-none" />
                <div class="flex-1 min-w-0 text-left -translate-x-[28px] sm:w-[168px] sm:min-w-[168px]">
                    <h3 class="text-[25px] sm:text-[29px] font-bold text-white mb-1 group-hover:text-stone-100 transition leading-tight whitespace-nowrap">
                        Focus Now
                    </h3>
                    <p class="text-[14px] sm:text-[16px] text-white/90 leading-[1.35]">
                        Your own personalized workspace.
                    </p>
                </div>
            </div>
        `;
    }

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
        let postsCardsHTML = '';
        if (previewPosts.length > 0 && window.TempoCommunity && typeof window.TempoCommunity.renderPostCardHTML === 'function') {
            postsCardsHTML = previewPosts.map(p => window.TempoCommunity.renderPostCardHTML(p)).join('');
        }

        return `
            <div class="space-y-6 sm:space-y-8 font-arimo" data-tempo-ui="entry-home">
                <!-- ==============================================================
                     UPPER SECTION: DESKTOP 2-COLUMN (LEFT: HERO + 2x2 GRID; RIGHT: COMMUNITY + BREATHING)
                     ============================================================== -->
                <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
                    <!-- LEFT COLUMN (Larger): Hero Card + 2x2 Tool Cards Grid -->
                    <div class="lg:col-span-7 xl:col-span-8 flex flex-col space-y-5">
                        <!-- Hero / Welcome Card -->
                        <div class="relative bg-[#FEFAF4] border border-[#EAE4DF] rounded-3xl sm:rounded-[28px] px-7 sm:px-9 py-5 sm:py-5.5 shadow-xs flex flex-col justify-between w-full max-w-[750px] xl:w-[750px] xl:h-[250px] xl:translate-x-[25px]" data-tempo-ui="entry-hero-card">
                            <div class="space-y-1.5">
                                <span class="text-[18.67px] sm:text-[21.33px] font-bold text-[#D99E87] block tracking-wide translate-y-[7px]">
                                    Welcome to Tempo
                                </span>
                                <h1 class="text-[32px] sm:text-[38px] lg:text-[43px] font-extrabold text-[#726D69] tracking-tight leading-[1.08] max-w-full xl:translate-y-[26px]">
                                    What do you need right now?
                                </h1>
                            </div>

                            <div class="pt-1">
                                <button type="button"
                                        id="btn-hero-figure-start"
                                        onclick="if (window.TempoApp && typeof window.TempoApp.openRoutingModal === 'function') { window.TempoApp.openRoutingModal(); } else if (window.TempoMode && typeof window.TempoMode.openHelpSelectionModal === 'function') { window.TempoMode.openHelpSelectionModal(); } else { const m = document.getElementById('modal-routing-selection'); if (m) { m.classList.remove('hidden'); document.body.classList.add('overflow-hidden'); } }"
                                        class="px-6 py-2.5 rounded-2xl bg-[#D99E87] hover:bg-[#C88D76] text-[#FEFAF4] font-bold text-sm sm:text-base shadow-sm transition inline-flex items-center space-x-2.5 cursor-pointer">
                                    <span>Help me figure out where to start</span>
                                    <span class="text-base sm:text-lg text-[#FEFAF4]">⟶</span>
                                </button>
                            </div>
                        </div>

                        <!-- 2x2 Grid of Tool Cards Below Hero -->
                        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-5 w-full max-w-[720px] mx-auto xl:ml-[40px]" data-tempo-ui="entry-tool-grid">
                            <!-- Tool 1: Quick Relief -->
                            ${renderQuickReliefCardHTML('xl:w-[350px]')}

                            <!-- Tool 2: Focus Now (Illustration on left, text on right) -->
                            ${renderFocusNowCardHTML('xl:w-[350px]')}

                            <!-- Tool 3: Learn & Solve -->
                            <div onclick="if (window.TempoApp) { window.TempoApp.navigateTo('learn'); } else { window.location.hash = '#learn'; }"
                                 class="bg-[#FBEDD9] border border-[#736F68] rounded-3xl overflow-hidden p-4 sm:p-5 flex items-center justify-between min-h-[175px] h-[175px] xl:w-[350px] shadow-[0_4px_10px_-2px_rgba(75,55,40,0.07),0_14px_28px_-5px_rgba(75,55,40,0.12)] hover:shadow-[0_6px_14px_-2px_rgba(75,55,40,0.09),0_20px_36px_-4px_rgba(75,55,40,0.16)] transition cursor-pointer group relative"
                                 title="Learn & Solve">
                                <div class="relative z-10 flex-1 min-w-0 pr-1">
                                    <h3 class="text-[22px] sm:text-[25px] font-bold text-[#736F68] mb-1 group-hover:text-[#5B5751] transition leading-tight whitespace-nowrap">
                                        Learn & Solve
                                    </h3>
                                    <p class="text-[14px] sm:text-[16px] text-[#736F68] leading-[1.35] max-w-[155px]">
                                        Tips and tools to help you cope.
                                    </p>
                                </div>
                                <img src="assets/learn-solve-mascot.png"
                                     alt="Learn & Solve Mascot"
                                     class="h-[100px] w-auto object-contain shrink-0 select-none pointer-events-none -mr-1 sm:-mr-2 translate-y-1" />
                            </div>

                            <!-- Tool 4: Tempo break -->
                            <div onclick="if (window.TempoTools && window.TempoTools.openBreak) { window.TempoTools.openBreak(); } else if (window.TempoFocusZone) { window.TempoFocusZone.openQuickEntry(); }"
                                 class="bg-[#D3DFE4] border border-[#736F68] rounded-3xl overflow-hidden p-4 sm:p-5 flex items-center justify-between min-h-[175px] h-[175px] xl:w-[350px] shadow-[0_4px_10px_-2px_rgba(75,55,40,0.07),0_14px_28px_-5px_rgba(75,55,40,0.12)] hover:shadow-[0_6px_14px_-2px_rgba(75,55,40,0.09),0_20px_36px_-4px_rgba(75,55,40,0.16)] transition cursor-pointer group relative"
                                 title="Tempo break">
                                <div class="relative z-10 flex-1 min-w-0 pr-1">
                                    <h3 class="text-[22px] sm:text-[25px] font-bold text-[#736D69] mb-1 group-hover:text-[#5B5551] transition leading-tight whitespace-nowrap">
                                        Tempo break
                                    </h3>
                                    <p class="text-[14px] sm:text-[16px] text-[#736D69] leading-[1.35] max-w-[155px]">
                                        Take a break with fun activities to unwind.
                                    </p>
                                </div>
                                <img src="assets/tempo-break-mascot.png"
                                     alt="Tempo break Mascot"
                                     class="h-[125px] w-auto object-contain shrink-0 select-none pointer-events-none -mr-1 sm:-mr-2 translate-y-1" />
                            </div>
                        </div>
                    </div>

                    <!-- RIGHT COLUMN: From the Tempo Community + Practice Breathing -->
                    <div class="lg:col-span-5 xl:col-span-4 flex flex-col space-y-[7px]">
                        <!-- Community Panel -->
                        <div class="bg-[#FEFAF4] border border-[#EAE4DF] rounded-3xl sm:rounded-[28px] p-4 sm:p-5 shadow-xs flex flex-col justify-between space-y-3.5" data-tempo-ui="entry-community-panel">
                            <!-- Header -->
                            <div class="flex items-center justify-between pb-0.5">
                                <div class="flex items-center space-x-2.5">
                                    <div class="w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-[#F6E6DE] flex items-center justify-center shrink-0">
                                        <img src="assets/comment-symbol.png"
                                             alt="Community"
                                             class="w-3.5 h-auto sm:w-4 object-contain select-none pointer-events-none" />
                                    </div>
                                    <h3 class="font-bold text-sm sm:text-base text-[#726D69] tracking-tight">
                                        From the Tempo Community
                                    </h3>
                                </div>
                                <button type="button"
                                        id="btn-see-all-posts"
                                        onclick="if (window.TempoCommunity && window.TempoCommunity.openCommunityModal) { window.TempoCommunity.openCommunityModal(); } else if (window.TempoApp) { window.TempoApp.navigateTo('posts'); }"
                                        class="px-3 py-1 rounded-full bg-[#F6E6DE] hover:bg-[#EED8CE] text-[#D99E87] text-xs font-bold transition flex items-center space-x-1 cursor-pointer">
                                    <span>See all</span>
                                    <span class="text-xs">→</span>
                                </button>
                            </div>

                            <!-- Horizontal divider below heading row -->
                            <div class="border-b border-[#EAE4DF] w-full -mt-1 mb-0.5"></div>

                            <!-- Social Peer Posts Container -->
                            <div id="homepage-community-posts-list" class="space-y-3 flex-1">
                                ${postsCardsHTML}
                            </div>
                        </div>

                        <!-- Practice Breathing Card (Underneath Community Panel) -->
                        <div onclick="if (window.TempoBreathing && window.TempoBreathing.openModal) { window.TempoBreathing.openModal(); } else if (window.TempoTriage && window.TempoTriage.openBoxBreathingModal) { window.TempoTriage.openBoxBreathingModal(); }"
                             class="bg-[#e7ece6] border border-[#000000] rounded-3xl p-4 sm:p-5 flex items-center justify-between transition cursor-pointer group relative overflow-hidden"
                             title="Practice Breathing">
                            <div class="pr-1 relative z-10 flex-1 min-w-0">
                                <h3 class="text-[20px] sm:text-[22px] xl:text-[23px] font-bold text-[#746f6a] mb-1 leading-tight whitespace-nowrap">
                                    Practice Breathing
                                </h3>
                                <p class="text-xs sm:text-sm text-[#746f6a] leading-relaxed max-w-[190px]">
                                    Take a deep breath and find your calm.
                                </p>
                            </div>
                            <img src="assets/practice-breathing-mascot.png"
                                 alt="Practice Breathing Mascot"
                                 class="w-[110px] h-[110px] sm:w-[120px] sm:h-[120px] object-contain shrink-0 select-none pointer-events-none -mr-0.5" />
                        </div>
                    </div>
                </div>

                <!-- ==============================================================
                     LOWER SECTION: HORIZONTAL 3-COLUMN ROW (SELF-CHECK • WORK PLAN • NOTES)
                     ============================================================== -->
                <div class="grid grid-cols-1 md:grid-cols-3 gap-6 pt-2" data-tempo-ui="entry-lower-section">
                    <!-- Lower Card 1: Self-check -->
                    <div onclick="window.TempoMode.openStrack('setup', { sourceContext: 'entry' });"
                         class="bg-[#e6ede7] border border-[#D2E7DF] rounded-3xl sm:rounded-[28px] p-6 flex flex-col justify-start items-center text-center shadow-xs relative min-h-[220px] md:h-[230px] overflow-hidden cursor-pointer group"
                         title="Self-check">
                        <div class="w-full text-center">
                            <span class="text-[11px] font-bold uppercase tracking-wider text-[#527668]/80 block mb-1 leading-tight text-center">
                                Self-check
                            </span>
                            <h2 class="text-xl sm:text-[22px] font-extrabold text-[#527668] leading-tight mb-1.5 tracking-tight text-center mx-auto max-w-[320px]">
                                How are you feeling today?
                            </h2>
                            <p class="text-xs sm:text-sm text-[#628A7A] leading-normal tracking-tight text-center mx-auto max-w-[320px]">
                                Take a moment to check in with yourself.
                            </p>
                        </div>
                        <div class="mt-auto flex justify-center items-center pt-2">
                            <img src="assets/self-check-mascot.png"
                                 alt="Self-check mascot"
                                 class="h-[88px] sm:h-[94px] w-auto object-contain select-none pointer-events-none" />
                        </div>
                    </div>

                    <!-- Lower Card 2: Work Plan -->
                    <div onclick="window.TempoApp.navigateTo('plan-workspace');"
                         class="bg-[#f7e5dc] border border-[#F0D5CC] rounded-3xl sm:rounded-[28px] p-6 flex flex-col justify-start items-center text-center shadow-xs relative min-h-[220px] md:h-[230px] overflow-hidden cursor-pointer group"
                         title="Work Plan">
                        <div class="w-full text-center">
                            <span class="text-[11px] font-bold uppercase tracking-wider text-[#e79370] block mb-1 text-center">
                                Work Plan
                            </span>
                            <h2 class="text-xl sm:text-[22px] font-extrabold text-[#e79370] leading-tight mb-1.5 text-center mx-auto max-w-[300px]">
                                What needs to get done?
                            </h2>
                            <p class="text-xs sm:text-sm text-[#e79370] leading-normal text-center mx-auto max-w-[300px]">
                                Organize your tasks and take things one step at a time.
                            </p>
                        </div>
                        <div class="mt-auto flex justify-center items-center pt-2">
                            <img src="assets/work-plan-mascot.png"
                                 alt="Work Plan mascot"
                                 class="h-[78px] sm:h-[84px] w-auto object-contain select-none pointer-events-none" />
                        </div>
                    </div>

                    <!-- Lower Card 3: Notes -->
                    <div onclick="if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') { window.TempoApp.navigateTo('tool-notes'); } else { window.location.hash = '#tool-notes'; }"
                         class="bg-[#faeddb] border border-[#F1DFC0] rounded-3xl sm:rounded-[28px] p-6 flex flex-col justify-start items-center text-center shadow-xs relative min-h-[220px] md:w-[350px] md:h-[230px] overflow-hidden cursor-pointer group"
                         title="Notes">
                        <div class="w-full text-center">
                            <span class="text-[11px] font-bold uppercase tracking-wider text-[#ca9555] block mb-1 text-center">
                                Notes
                            </span>
                            <h2 class="text-xl sm:text-[22px] font-extrabold text-[#ca9555] leading-tight mb-1.5 text-center mx-auto max-w-[280px]">
                                What is your notes for today?
                            </h2>
                            <p class="text-xs sm:text-sm text-[#ca9555] leading-normal text-center mx-auto max-w-[280px]">
                                Write down anything you want to remember.
                            </p>
                        </div>
                        <div class="mt-auto flex justify-center items-center pt-2">
                            <img src="assets/notes-mascot.png"
                                 alt="Notes mascot"
                                 class="h-[74px] sm:h-[80px] w-auto object-contain select-none pointer-events-none" />
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
                // Check for overdue/stale planned tasks from past dates or passed deadlines
                const allPlanned = confirmedPlan.plannedTasks || [];
                const staleTasks = allPlanned.filter(pt => {
                    if (!pt.task || pt.task.completed === true) return false;
                    const isOverdue = (window.TempoUrmodeFlow && window.TempoUrmodeFlow.isTaskOverdue)
                        ? window.TempoUrmodeFlow.isTaskOverdue(pt.task, confirmedPlan)
                        : (pt.dayDate && pt.dayDate < todayStr);
                    return isOverdue || (pt.dayDate && pt.dayDate < todayStr);
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

        const raw = profile?.display_name || profile?.full_name || profile?.preferred_name || profile?.first_name
            || user?.user_metadata?.display_name || user?.user_metadata?.full_name;

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
        const greetingHeading = displayName
            ? `Hi, ${escapeHTML(displayName)}, ready to get things done?`
            : 'Hi, ready to get things done?';

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
                                ? (window.t ? window.t('modes.urgent.notSetUpYet', {}, "You haven't set up your working plan yet") : "You haven't set up your working plan yet")
                                : (window.t ? window.t('modes.urgent.statePlanIncomplete', {}, "You're still setting up your plan.") : "You're still setting up your plan.")
                            }
                        </h3>
                        <span class="sr-only">You're still setting up your plan.</span>
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
            if (!pt.task || pt.task.completed === true) return false;
            const isOverdue = (window.TempoUrmodeFlow && window.TempoUrmodeFlow.isTaskOverdue)
                ? window.TempoUrmodeFlow.isTaskOverdue(pt.task, confirmedPlan)
                : (pt.dayDate && pt.dayDate < todayStr);
            return isOverdue || (pt.dayDate && pt.dayDate < todayStr);
        });

        const currentOverdue = staleTasks[0];
        const overdueTask = currentOverdue?.task;
        const taskName = overdueTask?.name || 'Overdue Task';

        return `
            <div class="urgent-card-now from-[#FFF9F5] border-[#FFD2BA] rounded-3xl p-6 sm:p-7 soft-card-shadow relative overflow-hidden transition flex flex-col justify-between" style="background-color: #faeddb; border: 1px solid #000000; min-height: 290px;" data-tempo-ui="urgent-task-now">
                <div class="relative z-10 space-y-3">
                    <!-- Badge Row: OVERDUE TASK -->
                    <div class="flex items-center justify-between mb-3.5">
                        <div class="flex items-center space-x-2">
                            <span class="w-2.5 h-2.5 rounded-full bg-amber-600 inline-block"></span>
                            <span class="px-4 py-1.5 rounded-full text-xs font-bold bg-amber-600 text-white shadow-2xs">
                                OVERDUE TASK
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
                            This task is overdue
                        </h3>
                    </div>

                    <!-- Status Description / Message -->
                    <div class="flex items-center space-x-2.5 my-2">
                        <div class="w-4 h-4 rounded border-2 border-amber-600/60 bg-transparent flex items-center justify-center shrink-0 text-amber-700 text-[10px] font-bold">!</div>
                        <p class="italic text-sm sm:text-base font-medium text-[#5D5954]">
                            Looks like this task has passed its due date. Would you like to clear it, mark it as done, or update it?
                        </p>
                    </div>

                    <!-- Overdue Task Info Box -->
                    <div class="p-3.5 bg-white/90 rounded-2xl border border-[#FFD2BA] text-xs text-amber-950 space-y-1.5 my-1">
                        <div class="flex items-center justify-between">
                            <span class="font-bold text-stone-800 text-sm sm:text-base">• ${escapeHTML(taskName)}</span>
                            <span class="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase tracking-wider bg-amber-100 text-amber-800 border border-amber-300">OVERDUE</span>
                        </div>
                        <div class="text-stone-500 text-[11px] flex flex-wrap items-center gap-2">
                            ${currentOverdue?.dayDate ? `<span>Was scheduled: ${escapeHTML(currentOverdue.dayLabel || currentOverdue.dayDate)}</span>` : ''}
                            ${overdueTask?.hasDeadline && overdueTask?.deadlineDate ? `<span>• Due: ${window.TempoI18n ? window.TempoI18n.formatDeadline(overdueTask.deadlineDate, overdueTask.deadlineTime) : formatHumanDeadline(overdueTask.deadlineDate, overdueTask.deadlineTime)}</span>` : ''}
                            ${overdueTask?.durationLabel ? `<span>• ~${escapeHTML(overdueTask.durationLabel)}</span>` : ''}
                        </div>
                    </div>
                </div>

                <!-- Action Buttons Row (Clear task, Mark as done, Edit task) -->
                <div class="relative z-10 pt-4 border-t border-[#E8D9C5] flex flex-wrap items-center gap-3">
                    <button type="button" onclick="window.TempoMode.clearOverdueTask('${overdueTask?.id}')"
                            class="px-5 py-2.5 rounded-2xl font-bold text-xs sm:text-sm bg-white hover:bg-rose-50 text-rose-700 border border-rose-200 shadow-2xs inline-flex items-center transition cursor-pointer">
                        Clear task
                    </button>
                    <button type="button" onclick="window.TempoMode.markOverdueTaskDone('${overdueTask?.id}')"
                            class="btn-primary btn-terracotta bg-emerald-600 px-5 py-2.5 rounded-2xl font-bold text-xs sm:text-sm shadow-sm inline-flex items-center transition cursor-pointer">
                        <span class="sr-only">Mark this task as finished - </span><span>Mark as done</span>
                    </button>
                    <button type="button" onclick="window.TempoApp.navigateTo('plan-workspace'); if (window.TempoPlanWorkspace && window.TempoPlanWorkspace.selectTask) { window.TempoPlanWorkspace.selectTask('${overdueTask?.id}'); }"
                            class="px-5 py-2.5 rounded-2xl font-bold text-xs sm:text-sm bg-white hover:bg-[#FAF7F4] text-[#6F6B68] border border-[#EAE4DF] shadow-2xs inline-flex items-center transition cursor-pointer">
                        <span class="sr-only">Update my plan - </span><span>Edit task</span>
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

        // 1. If viewing tomorrow's task explicitly
        if (sessionFlags.viewingTomorrowTask && futureTasks.length > 0) {
            const tomItem = futureTasks[0];
            const nextActionText = (tomItem.task && tomItem.task.subtasks && tomItem.task.subtasks.length > 0)
                ? (tomItem.task.subtasks.find(s => !s.completed)?.title || tomItem.task.subtasks[0].title)
                : (tomItem.task.description || "Begin focused work block.");
            const completedSubCount = (tomItem.task && tomItem.task.subtasks) ? tomItem.task.subtasks.filter(s => s.completed).length : 0;
            const totalSubCount = (tomItem.task && tomItem.task.subtasks) ? tomItem.task.subtasks.length : 0;
            const actionStepsLabel = totalSubCount > 0 ? `${completedSubCount} / ${totalSubCount} action steps` : '1 action step';
            const deadlineText = (tomItem.task && tomItem.task.hasDeadline && tomItem.task.deadlineDate)
                ? `${window.t ? window.t('modes.urgent.due', {}, 'Due') : 'Due'} ${window.TempoI18n ? window.TempoI18n.formatDeadline(tomItem.task.deadlineDate, tomItem.task.deadlineTime) : formatHumanDeadline(tomItem.task.deadlineDate, tomItem.task.deadlineTime)}`
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

                        <!-- Subtask Row / List -->
                        ${(tomItem.task && Array.isArray(tomItem.task.subtasks) && tomItem.task.subtasks.length > 0) ? `
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
                        ` : `
                            <div class="my-3">
                                <label class="flex items-center space-x-2.5 py-0.5 cursor-pointer select-none group" data-subtask-id="default">
                                    <input type="checkbox"
                                           id="tomorrow-subtask-checkbox-default"
                                           onclick="event.stopPropagation()"
                                           onchange="window.TempoMode.setSubtaskCompleted('${tomItem.task ? tomItem.task.id : ''}', 'default', this.checked)"
                                           class="w-4 h-4 rounded border-2 border-[#8C6C63]/80 text-[#D79277] focus:ring-[#D79277] cursor-pointer shrink-0"
                                           title="Mark step as done">
                                    <span class="italic text-sm sm:text-base font-medium transition text-[#5D5954]">
                                        ${escapeHTML(nextActionText)}
                                    </span>
                                </label>
                            </div>
                        `}

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
                            <span class="text-[#D0C0AC]">|</span>
                            <div class="flex items-center space-x-1.5">
                                <span>📝</span>
                                <span>${escapeHTML(actionStepsLabel)}</span>
                            </div>
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
                            I'll rest for now
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
                                    TODAY'S WORK DONE
                                </span>
                                <span class="sr-only">You're done for today. TODAY'S WORK DONE Tomorrow</span>
                            </div>
                        </div>

                        <div class="text-xs sm:text-sm font-semibold text-[#6F6B68] sr-only">
                            ${escapeHTML(greetingInfo ? greetingInfo.greetingText : 'Hi there 👋')}
                        </div>

                        <!-- Title Block -->
                        <div class="space-y-1">
                            <h3 class="font-heading text-2xl sm:text-[34px] font-extrabold text-[#484541] tracking-tight leading-snug">
                                You're all done for today! 🎉
                            </h3>
                        </div>

                        <!-- Status Description -->
                        <div class="flex items-center space-x-2.5 my-2">
                            <div class="w-4 h-4 rounded border-2 border-emerald-600/60 bg-emerald-100 flex items-center justify-center shrink-0 text-emerald-700 text-[10px] font-bold">✓</div>
                            <p class="italic text-sm sm:text-base font-medium text-[#5D5954]">
                                All done. You've earned some rest. Take it easy!
                            </p>
                        </div>
                    </div>

                    <!-- Action Row -->
                    <div class="relative z-10 pt-4 border-t border-[#E8D9C5] flex flex-wrap items-center gap-3">
                        <button onclick="window.TempoMode.showTomorrowTaskInCard()"
                                class="btn-primary btn-terracotta px-5 py-2.5 rounded-2xl font-bold text-xs sm:text-sm shadow-sm inline-flex items-center transition cursor-pointer">
                            <span>Let's do tomorrow's task →</span>
                        </button>
                        <button onclick="window.TempoMode.setRestingForToday(false)"
                                class="px-4 py-2 text-xs font-semibold text-[#6F6B68] hover:text-[#202124] underline cursor-pointer">
                            Back to overview
                        </button>
                    </div>
                </div>
            `;
        }

        // 3. Default: Choice between tomorrow's task and calling it a day
        const nextItem = futureTasks[0];
        const nextScheduleText = nextItem
            ? `${nextItem.dayLabel || nextItem.dayDate}${nextItem.startTime ? ` · ${nextItem.startTime}` : ''}`
            : 'Tomorrow';

        return `
            <div class="urgent-card-now from-[#FFF9F5] border-[#FFD2BA] rounded-3xl p-6 sm:p-7 soft-card-shadow relative overflow-hidden transition flex flex-col justify-between" style="background-color: #faeddb; border: 1px solid #000000; min-height: 290px;" data-tempo-ui="urgent-task-now">
                <div class="relative z-10 space-y-3">
                    <!-- Badge Row: TODAY'S WORK DONE -->
                    <div class="flex items-center justify-between mb-3.5">
                        <div class="flex items-center space-x-2">
                            <span class="w-2.5 h-2.5 rounded-full bg-emerald-600 inline-block"></span>
                            <span class="px-4 py-1.5 rounded-full text-xs font-bold bg-emerald-700 text-white shadow-2xs">
                                TODAY'S WORK DONE
                            </span>
                            <span class="sr-only">You're done for today. TODAY'S WORK DONE Tomorrow</span>
                        </div>
                    </div>

                    <div class="text-xs sm:text-sm font-semibold text-[#6F6B68] sr-only">
                        ${escapeHTML(greetingInfo ? greetingInfo.greetingText : 'Hi there 👋')}
                    </div>

                    <!-- Title Block -->
                    <div class="space-y-1">
                        <h3 class="font-heading text-2xl sm:text-[34px] font-extrabold text-[#484541] tracking-tight leading-snug">
                            You're all done for today! 🎉
                        </h3>
                    </div>

                    <!-- Status Description -->
                    <div class="flex items-center space-x-2.5 my-2">
                        <div class="w-4 h-4 rounded border-2 border-emerald-600/60 bg-emerald-100 flex items-center justify-center shrink-0 text-emerald-700 text-[10px] font-bold">✓</div>
                        <p class="italic text-sm sm:text-base font-medium text-[#5D5954]">
                            You've made it through today's tasks. Want to get a head start on tomorrow, or call it a day?
                        </p>
                    </div>

                    <!-- Next Planned Work Preview Box -->
                    <div class="p-3.5 bg-white/90 border border-[#FFD2BA] rounded-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs my-1">
                        <div class="space-y-0.5">
                            <span class="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Next planned work:</span>
                            <div class="font-bold text-sm text-[#202124]">${escapeHTML(nextScheduleText)}</div>
                            ${nextItem ? `<p class="text-[#6F6B68] text-[11px]">${escapeHTML(nextItem.task.name)}</p>` : ''}
                        </div>
                        ${nextItem ? `
                            <button onclick="window.TempoMode.showTomorrowTaskInCard()"
                                    class="px-4 py-2 rounded-xl border border-[#FFD2BA] bg-white font-semibold text-xs text-gray-700 hover:bg-stone-50 transition self-start sm:self-auto cursor-pointer">
                                Preview tomorrow →
                            </button>
                        ` : ''}
                    </div>
                </div>

                <!-- Action Row -->
                <div class="relative z-10 pt-4 border-t border-[#E8D9C5] flex flex-wrap items-center gap-3">
                    <button onclick="window.TempoMode.showTomorrowTaskInCard()"
                            class="btn-primary btn-terracotta px-5 py-2.5 rounded-2xl font-bold text-xs sm:text-sm shadow-sm inline-flex items-center transition cursor-pointer">
                        <span>Let's do tomorrow's task →</span>
                    </button>
                    <button onclick="window.TempoMode.setRestingForToday(true)"
                            class="px-5 py-2.5 rounded-2xl font-bold text-xs sm:text-sm bg-white hover:bg-[#FAF7F4] text-[#6F6B68] border border-[#EAE4DF] shadow-2xs inline-flex items-center transition cursor-pointer">
                        <span>I'll rest for now</span>
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

        // Subtask / next concrete action logic
        let nextActionText = "Begin focused preliminary work block.";
        let actionStepsLabel = "1 action step";
        if (nowItem && nowItem.task && nowItem.task.subtasks && nowItem.task.subtasks.length > 0) {
            const incompleteSubtasks = nowItem.task.subtasks.filter(s => !s.completed);
            const completedSubtasksCount = nowItem.task.subtasks.filter(s => s.completed).length;
            const totalSubtasksCount = nowItem.task.subtasks.length;
            nextActionText = incompleteSubtasks.length > 0 ? incompleteSubtasks[0].title : (nowItem.task.description || "All preliminary steps completed.");
            actionStepsLabel = `${completedSubtasksCount} / ${totalSubtasksCount} action steps`;
        } else if (nowItem && nowItem.task && nowItem.task.description) {
            nextActionText = nowItem.task.description;
        }

        const deadlineText = (nowItem && nowItem.task && nowItem.task.hasDeadline)
            ? `${window.t ? window.t('modes.urgent.due', {}, 'Due') : 'Due'} ${window.TempoI18n ? window.TempoI18n.formatDeadline(nowItem.task.deadlineDate, nowItem.task.deadlineTime) : formatHumanDeadline(nowItem.task.deadlineDate, nowItem.task.deadlineTime)}`
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

                        <!-- Subtask Row / List -->
                        ${(nowItem.task && Array.isArray(nowItem.task.subtasks) && nowItem.task.subtasks.length > 0) ? `
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
                        ` : `
                            <div class="my-3">
                                <label class="flex items-center space-x-2.5 py-0.5 cursor-pointer select-none group" data-subtask-id="default">
                                    <input type="checkbox"
                                           id="subtask-checkbox-default"
                                           onclick="event.stopPropagation()"
                                           onchange="window.TempoMode.setSubtaskCompleted('${nowItem.task ? nowItem.task.id : ''}', 'default', this.checked)"
                                           class="w-4 h-4 rounded border-2 border-[#8C6C63]/80 text-[#D79277] focus:ring-[#D79277] cursor-pointer shrink-0"
                                           title="Mark step as done">
                                    <span class="italic text-sm sm:text-base font-medium transition text-[#5D5954]">
                                        ${escapeHTML(nextActionText)}
                                    </span>
                                </label>
                            </div>
                        `}

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
                            <span class="text-[#D0C0AC]">|</span>
                            <div class="flex items-center space-x-1.5">
                                <span>📝</span>
                                <span>${escapeHTML(actionStepsLabel)}</span>
                            </div>
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
                            <span class="sr-only">View task - Xem công việc - </span><span>Edit task</span>
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

        let noteText = "Drink more than 3 cups of water";
        try {
            const savedNote = localStorage.getItem('tempo_recovery_note');
            if (savedNote) {
                const parsed = JSON.parse(savedNote);
                if (parsed && (parsed.content || parsed.text)) {
                    noteText = parsed.content || parsed.text;
                }
            }
        } catch (e) {}

        const noteCardHTML = `
            <!-- 1. NOTE Card Section (+10px taller: min-h-[96px] with py-7 sm:py-7.5) -->
            <div class="space-y-1.5 cursor-pointer"
                 onclick="if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') { window.TempoApp.navigateTo('tool-notes'); } else { window.location.hash = '#tool-notes'; }">
                <div class="flex items-center justify-between pb-0.5">
                    <div class="flex items-center space-x-1.5 text-xs font-extrabold uppercase tracking-wider text-[#D79277]">
                        <span>💡</span>
                        <span>NOTE</span>
                    </div>
                    <a role="button" tabindex="0"
                       onclick="event.stopPropagation(); if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') { window.TempoApp.navigateTo('tool-notes'); } else { window.location.hash = '#tool-notes'; }"
                       class="px-2.5 py-0.5 rounded-full text-xs font-bold text-[#D79277] hover:text-[#B85D38] bg-[#FDF2EC] hover:bg-[#FBE8DE] border border-[#D79277]/30 transition cursor-pointer flex items-center space-x-1"
                       title="Create your notes">
                        <span>Create your notes</span>
                        <span class="text-[10px]">→</span>
                    </a>
                </div>

                <!-- Note Card: min-h-[96px] (+10px taller than previous 86px) -->
                <div role="button" tabindex="0"
                     onclick="event.stopPropagation(); if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') { window.TempoApp.navigateTo('tool-notes'); } else { window.location.hash = '#tool-notes'; }"
                     onkeydown="if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); event.stopPropagation(); if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') { window.TempoApp.navigateTo('tool-notes'); } else { window.location.hash = '#tool-notes'; } }"
                     class="bg-[#FCF2E9] border border-[#D79277]/60 hover:border-[#D79277] hover:bg-[#FAF0E7] hover:shadow-md rounded-2xl px-5 py-7 sm:py-7.5 min-h-[96px] flex items-center soft-card-shadow cursor-pointer transition duration-150 select-none group"
                     title="Tool Notes"
                     data-tempo-ui="dashboard-note-card">
                    <p class="text-sm font-semibold text-[#B85D38] leading-relaxed group-hover:text-[#A74E2A] transition">
                        ${escapeHTML(noteText)}
                    </p>
                </div>
            </div>
        `;

        const changeModePromptHTML = `
            <!-- 3. Mode Change Prompt & Large Action Button -->
            <div class="pt-2 flex flex-col items-center text-center space-y-2.5">
                <p class="text-sm sm:text-[15px] font-bold text-[#484541]">
                    Are things feeling less urgent now?
                </p>
                <button type="button" 
                        onclick="window.TempoMode.openChangeModeModal()"
                        class="w-full max-w-[280px] py-3 rounded-2xl font-bold text-sm sm:text-base bg-[#D79277] hover:bg-[#C68166] text-white shadow-[0_4px_12px_rgba(215,146,119,0.35)] hover:shadow-[0_6px_16px_rgba(215,146,119,0.45)] border border-[#C68166]/40 transition transform hover:-translate-y-0.5 cursor-pointer">
                    Change my mode
                </button>
            </div>
        `;

        const hasAnyPlanTasks = confirmedPlan && (
            (Array.isArray(confirmedPlan.plannedTasks) && confirmedPlan.plannedTasks.length > 0) ||
            (Array.isArray(confirmedPlan.unarrangedTasks) && confirmedPlan.unarrangedTasks.length > 0) ||
            (Array.isArray(confirmedPlan.unallocatedTasks) && confirmedPlan.unallocatedTasks.length > 0) ||
            (Array.isArray(confirmedPlan.tasks) && confirmedPlan.tasks.length > 0)
        );

        if (state === 'PLAN_INCOMPLETE' || !confirmedPlan || !hasAnyPlanTasks) {
            return `
                ${noteCardHTML}
                <div class="urgent-working-plan-card bg-white border border-[#EAE4DF] rounded-3xl p-5 sm:py-5 sm:px-6 soft-card-shadow space-y-3">
                    <div class="flex items-center justify-between pb-1">
                        <h3 class="font-heading text-lg sm:text-xl font-extrabold text-[#484541] tracking-tight">
                            <span class="sr-only">Your plan for today - </span>Your Working Plan
                        </h3>
                        <button onclick="window.TempoApp.navigateTo('emergency'); if (window.TempoEmergencyFlow && window.TempoEmergencyFlow.goToStage) { window.TempoEmergencyFlow.goToStage('${currentStage || 'entry'}'); }"
                                class="text-xs font-bold text-[#D79277] hover:text-[#B85D38] flex items-center space-x-1 transition cursor-pointer">
                            <span>Resume Setup</span>
                            <span>→</span>
                        </button>
                    </div>
                    <div class="urgent-working-plan-empty-body">
                        <div class="p-4 bg-stone-50 border border-stone-200/60 rounded-2xl text-xs text-[#6F6B68] space-y-2">
                            <div class="font-bold text-[#202124]">Plan setup in progress</div>
                            <p>Your task schedule and timeline will appear here once you finalize your urgent plan.</p>
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

        if (planTasks.length === 0) {
            return `
                ${noteCardHTML}
                <div class="urgent-working-plan-card bg-white border border-[#EAE4DF] rounded-3xl p-5 sm:py-5 sm:px-6 soft-card-shadow space-y-3">
                    <div class="flex items-center justify-between pb-1">
                        <h3 class="font-heading text-lg sm:text-xl font-extrabold text-[#484541] tracking-tight">
                            <span class="sr-only">Your plan for today - </span>Your Working Plan
                        </h3>
                        <button onclick="window.TempoApp.navigateTo('plan-workspace');"
                                class="px-3.5 py-1 rounded-full text-xs font-bold bg-[#D79277] hover:bg-[#C68166] text-white shadow-2xs transition cursor-pointer">
                            <span class="sr-only">View / Edit Plan - </span><span>Adjust Plan</span>
                        </button>
                    </div>
                    <div class="urgent-working-plan-empty-body">
                        <div class="p-4 bg-stone-50 border border-stone-200/60 rounded-2xl text-xs text-[#6F6B68] space-y-2">
                            <div class="font-bold text-[#202124]">Nothing scheduled today</div>
                            <p>Your Urgent Plan has no scheduled tasks.</p>
                        </div>
                    </div>
                    <div class="urgent-working-plan-footer pt-4 border-t border-stone-100 flex items-center justify-between text-xs text-[#8C8782]">
                        <span>0 tasks</span>
                        <button onclick="window.TempoApp.navigateTo('plan-workspace');" class="hover:text-[#202124] underline cursor-pointer">
                            View Plan Schedule →
                        </button>
                    </div>
                </div>
                ${changeModePromptHTML}
            `;
        }

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
            ${noteCardHTML}
            <div class="urgent-working-plan-card bg-white border border-[#EAE4DF] rounded-3xl p-5 sm:py-5 sm:px-6 soft-card-shadow flex flex-col">
                <!-- Header & Progress Section (Fixed / Stationary) -->
                <div class="shrink-0 space-y-2.5 pb-2.5">
                    <div class="flex items-center justify-between pb-0.5">
                        <h3 class="font-heading text-lg sm:text-xl font-extrabold text-[#484541] tracking-tight">
                            <span class="sr-only">Your plan for today - </span>Your Working Plan
                        </h3>
                        <button onclick="window.TempoApp.navigateTo('plan-workspace');"
                                class="px-3.5 py-1 rounded-full text-xs font-bold bg-[#D79277] hover:bg-[#C68166] text-white shadow-2xs transition cursor-pointer">
                            <span class="sr-only">View / Edit Plan - </span><span>Adjust Plan</span>
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
                    ${planTasks.map((item, idx) => {
                        const isDone = item.task && item.task.completed === true;
                        const isUnscheduled = !!item.isUnscheduled;
                        const isNow = !isDone && !isUnscheduled && nowItem && item.task && item.task.id === nowItem.task.id;
                        const isLast = idx === planTasks.length - 1;

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
                            metaText = `Due: ${window.TempoI18n ? window.TempoI18n.formatDeadline(item.task.deadlineDate, item.task.deadlineTime) : formatHumanDeadline(item.task.deadlineDate, item.task.deadlineTime)}`;
                        } else if (item.task && item.task.durationLabel) {
                            metaText = `~${item.task.durationLabel}`;
                        } else if (item.task && item.task.isUnknownDuration) {
                            metaText = 'Time not estimated';
                        } else if (isUnscheduled) {
                            metaText = (window.TempoI18n?.getCurrentLanguage?.() === 'vi' ? 'Chưa lên lịch' : 'Not scheduled');
                        }

                        return `
                            <div class="urgent-timeline-item py-2.5 sm:py-3 px-3.5 sm:px-4 rounded-2xl border border-[#E8E2DD] bg-[#FFFFFF] ${isNow ? 'hover:border-[#D79277]/40' : 'hover:border-stone-300'} transition space-y-1 relative">
                                ${!isLast ? '<div class="urgent-timeline-line hidden"></div>' : ''}
                                
                                <div class="flex items-center justify-between">
                                    <div class="flex items-center space-x-2.5 min-w-0 flex-1 mr-2 cursor-pointer" onclick="window.TempoMode.toggleTaskCompletion('${item.task.id}')">
                                        ${bulletHTML}
                                        <h4 class="font-bold text-sm sm:text-base truncate ${isDone ? 'line-through text-stone-400' : 'text-[#484541]'}">
                                            ${escapeHTML(item.task.name)}
                                        </h4>
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
                                <div class="pl-6.5 text-[11px] sm:text-xs text-[#8C8782] flex items-center space-x-3">
                                    ${metaText ? `<span>${escapeHTML(metaText)}</span>` : ''}
                                    ${subtaskCount ? `${metaText ? '<span>•</span>' : ''}<span>${escapeHTML(subtaskCount)}</span>` : ''}
                                </div>
                            </div>
                        `;
                    }).join('')}
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
        return `
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-5 w-full urgent-support-row" data-tempo-ui="urgent-support">
                <!-- Tool 1: Quick Relief -->
                ${renderQuickReliefCardHTML('urgent-card-overwhelmed')}

                <!-- Tool 2: Focus Now -->
                ${renderFocusNowCardHTML('urgent-card-focus-now')}
            </div>
        `;
    }

    // -------------------------------------------------------------------------
    // LOWER SCROLL SECTION: Enjoy Tempo Tools + From the Tempo Community
    // -------------------------------------------------------------------------
    function renderEmodeLowerSection() {
        return `
            <div id="enjoy-tempo-tools" class="pt-8 border-t border-[#D0E0D7] mt-8" data-tempo-ui="urgent-lower-section">
                <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">

                    <!-- LEFT COLUMN: Enjoy Tempo Tools (2x2 Grid + Self-Check Banner) -->
                    <div class="lg:col-span-7 flex flex-col space-y-4">
                        
                        <h2 class="text-2xl sm:text-[28px] font-extrabold text-[#726D69] tracking-tight">
                            Enjoy Tempo Tools
                        </h2>

                        <!-- 2x2 Grid of Tool Cards -->
                        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 w-full">
                            
                            <!-- Tool 1: Learn & Solve -->
                            <div onclick="if (window.TempoApp) { window.TempoApp.navigateTo('learn'); } else { window.location.hash = '#learn'; }"
                                 class="bg-[#FBEDD9] border border-[#736F68] rounded-3xl overflow-hidden p-4 sm:p-5 flex items-center justify-between min-h-[175px] h-[175px] shadow-[0_4px_10px_-2px_rgba(75,55,40,0.07),0_14px_28px_-5px_rgba(75,55,40,0.12)] hover:shadow-[0_6px_14px_-2px_rgba(75,55,40,0.09),0_20px_36px_-4px_rgba(75,55,40,0.16)] transition cursor-pointer group relative" title="Learn & Solve">
                                <div class="relative z-10 flex-1 min-w-0 pr-1">
                                    <h3 class="text-[22px] sm:text-[25px] font-bold text-[#736F68] mb-1 group-hover:text-[#5B5751] transition leading-tight whitespace-nowrap">
                                        Learn &amp; Solve
                                    </h3>
                                    <p class="text-[14px] sm:text-[16px] text-[#736F68] leading-[1.35] max-w-[155px]">
                                        Tips and tools to help you cope.
                                    </p>
                                </div>
                                <img src="assets/learn-solve-mascot.png" alt="Learn & Solve Mascot" class="h-[105px] w-auto object-contain shrink-0 select-none pointer-events-none -mr-1 sm:-mr-2 translate-y-1" />
                            </div>

                            <!-- Tool 2: Tempo break -->
                            <div onclick="if (window.TempoTools && window.TempoTools.openBreak) { window.TempoTools.openBreak(); } else if (window.TempoFocusZone) { window.TempoFocusZone.openQuickEntry(); }"
                                 class="bg-[#D3DFE4] border border-[#736F68] rounded-3xl overflow-hidden p-4 sm:p-5 flex items-center justify-between min-h-[175px] h-[175px] shadow-[0_4px_10px_-2px_rgba(75,55,40,0.07),0_14px_28px_-5px_rgba(75,55,40,0.12)] hover:shadow-[0_6px_14px_-2px_rgba(75,55,40,0.09),0_20px_36px_-4px_rgba(75,55,40,0.16)] transition cursor-pointer group relative" title="Tempo break">
                                <div class="relative z-10 flex-1 min-w-0 pr-1">
                                    <h3 class="text-[22px] sm:text-[25px] font-bold text-[#736D69] mb-1 group-hover:text-[#5B5551] transition leading-tight whitespace-nowrap">
                                        Tempo break
                                    </h3>
                                    <p class="text-[14px] sm:text-[16px] text-[#736D69] leading-[1.35] max-w-[155px]">
                                        Take a break with fun activities to unwind.
                                    </p>
                                </div>
                                <img src="assets/tempo-break-mascot.png" alt="Tempo break Mascot" class="h-[125px] w-auto object-contain shrink-0 select-none pointer-events-none -mr-1 sm:-mr-2 translate-y-1" />
                            </div>

                            <!-- Tool 3: Practice Breathing -->
                            <div onclick="if (window.TempoTriage && window.TempoTriage.openBoxBreathingModal) { window.TempoTriage.openBoxBreathingModal(); } else if (window.TempoBreathing && window.TempoBreathing.openModal) { window.TempoBreathing.openModal(); }"
                                 class="bg-[#E6EDE7] border border-[#736F68] rounded-3xl overflow-hidden p-4 sm:p-5 flex items-center justify-between min-h-[175px] h-[175px] shadow-[0_4px_10px_-2px_rgba(75,55,40,0.07),0_14px_28px_-5px_rgba(75,55,40,0.12)] hover:shadow-[0_6px_14px_-2px_rgba(75,55,40,0.09),0_20px_36px_-4px_rgba(75,55,40,0.16)] transition cursor-pointer group relative" title="Practice Breathing">
                                <div class="relative z-10 flex-1 min-w-0 pr-1">
                                    <h3 class="text-[18px] sm:text-[18.5px] font-bold text-[#736F68] mb-1 group-hover:text-[#5B5751] transition leading-tight whitespace-nowrap">
                                        Practice Breathing
                                    </h3>
                                    <p class="text-[14px] sm:text-[16px] text-[#736F68] leading-[1.35] max-w-[155px]">
                                        Take a deep breath and find your calm.
                                    </p>
                                </div>
                                <img src="assets/practice-breathing-mascot.png" alt="Practice Breathing Mascot" class="h-[120px] w-auto object-contain shrink-0 select-none pointer-events-none -mr-1" />
                            </div>

                            <!-- Tool 4: Create Notes -->
                            <div onclick="if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') { window.TempoApp.navigateTo('tool-notes'); } else { window.location.hash = '#tool-notes'; }"
                                 class="bg-[#F9E8E2] border border-[#736F68] rounded-3xl overflow-hidden p-4 sm:p-5 flex items-center justify-between min-h-[175px] h-[175px] shadow-[0_4px_10px_-2px_rgba(75,55,40,0.07),0_14px_28px_-5px_rgba(75,55,40,0.12)] hover:shadow-[0_6px_14px_-2px_rgba(75,55,40,0.09),0_20px_36px_-4px_rgba(75,55,40,0.16)] transition cursor-pointer group relative" title="Create Notes">
                                <div class="relative z-10 flex-1 min-w-0 pr-1">
                                    <h3 class="text-[22px] sm:text-[25px] font-bold text-[#8C6C63] mb-1 group-hover:text-[#72554D] transition leading-tight whitespace-nowrap">
                                        Create Notes
                                    </h3>
                                    <p class="text-[14px] sm:text-[16px] text-[#8C6C63] leading-[1.35] max-w-[155px]">
                                        Write down anything you want to remember.
                                    </p>
                                </div>
                                <img src="assets/notes-mascot.png" alt="Create Notes Mascot" class="h-[115px] w-auto object-contain shrink-0 select-none pointer-events-none -mr-1" />
                            </div>

                        </div>

                        <!-- Lower Full-Width Banner: How are you feeling today? (Reduced width by additional 40px, Compact Centered Content Group, bg #e8ecf1) -->
                        <div onclick="if (window.TempoMode && typeof window.TempoMode.openStrack === 'function') { window.TempoMode.openStrack('open', { sourceContext: 'emergency' }); } else if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') { window.TempoApp.navigateTo('stress-check'); } else { window.location.hash = '#stress-check'; }"
                             class="bg-[#e8ecf1] border border-[#708088] rounded-3xl overflow-hidden p-5 sm:p-6 flex items-center justify-center min-h-[135px] w-[calc(100%-110px)] mx-auto shadow-[0_4px_10px_-2px_rgba(75,55,40,0.07),0_14px_28px_-5px_rgba(75,55,40,0.12)] hover:shadow-[0_6px_14px_-2px_rgba(75,55,40,0.09),0_20px_36px_-4px_rgba(75,55,40,0.16)] transition cursor-pointer group relative" title="Self-check">
                            <div class="flex items-center justify-center gap-5 sm:gap-7 max-w-full">
                                <div class="text-left min-w-0 sm:shrink-0">
                                    <h3 class="text-2xl sm:text-[26px] font-extrabold text-[#527668] mb-1 leading-tight tracking-tight">
                                        How are you feeling today?
                                    </h3>
                                    <p class="text-sm sm:text-base text-[#628A7A] leading-snug">
                                        Take a moment to check in with yourself.
                                    </p>
                                </div>
                                <img src="assets/self-check-mascot.png" alt="Self-check Mascot" class="h-[95px] sm:h-[110px] w-auto object-contain shrink-0 select-none pointer-events-none" />
                            </div>
                        </div>

                    </div>

                    <!-- RIGHT COLUMN: From the Tempo Community -->
                    <div class="lg:col-span-5">
                        ${renderTempoPostsSection()}
                    </div>

                </div>
            </div>
        `;
    }

    // -------------------------------------------------------------------------
    // TEMPO POSTS COMPONENT (Lightweight Community Social Feed Previews)
    // -------------------------------------------------------------------------
    function renderTempoPostsSection() {
        let posts = (window.TempoCommunity && typeof window.TempoCommunity.getAllPosts === 'function')
            ? window.TempoCommunity.getAllPosts()
            : [];
        if (!Array.isArray(posts) || posts.length === 0) {
            if (window.TempoCommunity && typeof window.TempoCommunity.getInitialPosts === 'function') {
                posts = window.TempoCommunity.getInitialPosts();
            }
        }
        const previewPosts = (Array.isArray(posts) && posts.length > 0) ? posts.slice(0, 2) : [];
        let postsCardsHTML = '';
        if (previewPosts.length > 0 && window.TempoCommunity && typeof window.TempoCommunity.renderPostCardHTML === 'function') {
            postsCardsHTML = previewPosts.map(p => window.TempoCommunity.renderPostCardHTML(p)).join('');
        }

        return `
            <div class="urgent-section-posts bg-[#FEFAF4] border border-[#EAE4DF] rounded-3xl p-5 sm:p-6 soft-card-shadow flex flex-col space-y-4" data-tempo-ui="urgent-posts">
                <!-- Header -->
                <div class="flex items-center justify-between pb-1 border-b border-[#EAE4DF]">
                    <div class="flex items-center space-x-2.5">
                        <div class="w-8 h-8 rounded-full bg-[#F6E6DE] flex items-center justify-center shrink-0">
                            <img src="assets/comment-symbol.png" alt="Community" class="w-4 h-4 object-contain">
                        </div>
                        <h3 class="font-extrabold text-base sm:text-lg text-[#726D69] tracking-tight">
                            <span class="sr-only">Tempo Posts - </span>From the Tempo Community
                        </h3>
                    </div>
                    <button type="button" 
                            onclick="if (window.TempoCommunity && typeof window.TempoCommunity.openCommunityModal === 'function') { window.TempoCommunity.openCommunityModal(); } else if (window.TempoApp) { window.TempoApp.navigateTo('posts'); }" 
                            class="px-3.5 py-1 rounded-full bg-[#F6E6DE] hover:bg-[#EED8CE] text-[#D99E87] text-xs font-bold transition flex items-center space-x-1 cursor-pointer">
                        <span>See all</span>
                        <span class="text-xs">→</span>
                    </button>
                </div>

                <!-- Posts list -->
                <div id="urgent-community-posts-list" class="space-y-3">
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
        openStrack('setup');
    }

    function handleSelfCheckAction(action) {
        openStrack(action);
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

        syncModeSelectorDOM(MODES.RECOVERY);

        // Also trigger community posts preview sync
        if (window.TempoCommunity && typeof window.TempoCommunity.renderRecoveryPreview === 'function') {
            window.TempoCommunity.renderRecoveryPreview();
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
        if (activeSharedTool === 'ucheck') {
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
     * 4. 'Your Working Plan' task item completion toggle
     */
    async function setTaskCompletionStatus(taskId, isCompleted, options = {}) {
        if (!taskId) return false;
        if (isTaskActionSubmitting) return false;
        isTaskActionSubmitting = true;

        let previousCompleted = null;
        let previousInProgress = null;
        let matchedTask = null;
        const sTaskId = String(taskId);

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
                throw new Error("Active Working Plan not found.");
            }

            // 2. Identify target task by stable ID across all plan task collections
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

            // Also check flowPlan if distinct instance
            if (!matchedTask && flowPlan && flowPlan !== plan) {
                if (Array.isArray(flowPlan.plannedTasks)) {
                    const pt = flowPlan.plannedTasks.find(item => item.task && String(item.task.id) === sTaskId);
                    if (pt && pt.task) matchedTask = pt.task;
                }
                if (!matchedTask && Array.isArray(flowPlan.unarrangedTasks)) {
                    const u = flowPlan.unarrangedTasks.find(item => String(item && item.task ? item.task.id : item.id) === sTaskId);
                    if (u) matchedTask = u.task || u;
                }
                if (!matchedTask && Array.isArray(flowPlan.tasks)) {
                    matchedTask = flowPlan.tasks.find(t => t && String(t.id) === sTaskId);
                }
            }

            if (!matchedTask) {
                throw new Error("Task not found in active Working Plan.");
            }

            // Snapshot previous state for atomic rollback on persistence failure
            previousCompleted = matchedTask.completed;
            previousInProgress = matchedTask.isInProgress ?? matchedTask.in_progress ?? false;

            const targetCompleted = (typeof isCompleted === 'boolean') ? isCompleted : !previousCompleted;
            const targetInProgress = targetCompleted ? false : (matchedTask.isInProgress || matchedTask.in_progress || false);

            const isOverdue = !!(options.isOverdue || (window.TempoUrmodeFlow && window.TempoUrmodeFlow.isTaskOverdue && window.TempoUrmodeFlow.isTaskOverdue(matchedTask, plan)));

            // 3. Mutate task in active plan
            matchedTask.completed = targetCompleted;
            matchedTask.isInProgress = targetInProgress;
            matchedTask.in_progress = targetInProgress;

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
                }
            }

            // 6. Verify persistence succeeded
            const verifiedPlan = window.TempoPlanStore && typeof window.TempoPlanStore.getActivePlan === 'function'
                ? window.TempoPlanStore.getActivePlan('emergency')
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

            // 8. Recompute and refresh active mode home (Urmode dashboard)
            renderActiveModeHome();
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
            if (!Array.isArray(matchedTask.subtasks) || matchedTask.subtasks.length === 0) {
                const defaultTitle = matchedTask.description || "Begin focused preliminary work block.";
                const newSubId = (sSubtaskId !== 'default') ? sSubtaskId : ('sub-' + Date.now());
                matchedTask.subtasks = [{
                    id: newSubId,
                    title: defaultTitle,
                    completed: targetCompleted
                }];
            } else {
                let foundSub = null;
                if (sSubtaskId === 'default') {
                    foundSub = matchedTask.subtasks[0];
                } else {
                    foundSub = matchedTask.subtasks.find(s => String(s.id) === sSubtaskId);
                }

                if (foundSub) {
                    foundSub.completed = targetCompleted;
                } else {
                    matchedTask.subtasks.push({
                        id: sSubtaskId,
                        title: "Action step",
                        completed: targetCompleted
                    });
                }
            }

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

    async function clearOverdueTask(taskId) {
        if (isTaskActionSubmitting) return;
        if (!confirm("Are you sure you want to remove this task from your Working Plan?")) {
            return;
        }

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
        getActiveContext,
        hasActiveContext,
        getSourceContext,
        setSourceContext,
        getActiveSharedTool,
        getPendingIntent,
        setPendingIntent,
        clearPendingIntent,
        transitionContext,
        requestContext,
        openUcheck,
        returnToSourceContext,
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
        openStrack,
        getDestinationDisplayName,
        isValidPendingIntent,
        getRecentlyState,
        setRecentlyState,
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
        clearOverdueTask,
        markOverdueTaskDone,
        showTomorrowTaskInCard,
        setRestingForToday,
        getActiveHomeState: () => currentActiveHomeState,
        EPLAN_STATES
    };
})();

