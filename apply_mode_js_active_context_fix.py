with open('mode.js', 'rb') as f:
    content = f.read().decode('utf-8')

# 1. Update init()
target1 = """            if (authState === 'AUTH_LOADING') {
                if (savedMode === MODES.EMERGENCY || savedMode === MODES.RECOVERY) {
                    activeContext = savedMode;
                    sourceContext = savedMode;
                } else if (savedMode === MODES.UNCLEAR) {
                    activeContext = MODES.UNCLEAR;
                    sourceContext = getOriginatingMode() || 'entry';
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
                    activeContext = MODES.UNCLEAR;
                    sourceContext = getOriginatingMode() || 'entry';
                } else {
                    // Authenticated user with no established active context -> Entry Home
                    activeContext = null;
                    sourceContext = 'entry';
                    localStorage.setItem('tempo_current_mode', MODES.DEFAULT);
                }
            }"""

replacement1 = """            if (authState === 'AUTH_LOADING') {
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
            }"""

assert target1 in content, 'target1 not found in mode.js'
content = content.replace(target1, replacement1, 1)

# 2. Update init() Rmode entry check
target2 = """        if (activeContext === MODES.RECOVERY) {
            if (window.TempoRecoverySetup && typeof window.TempoRecoverySetup.handleRmodeEntry === 'function') {
                window.TempoRecoverySetup.handleRmodeEntry();"""

replacement2 = """        if (activeContext === MODES.RECOVERY && activeSharedTool !== 'ucheck') {
            if (window.TempoRecoverySetup && typeof window.TempoRecoverySetup.handleRmodeEntry === 'function') {
                window.TempoRecoverySetup.handleRmodeEntry();"""

assert target2 in content, 'target2 not found in mode.js'
content = content.replace(target2, replacement2, 1)

# 3. Update transitionContext
target3 = """    function transitionContext(targetContext, options = {}) {
        if (targetContext === 'urgent') targetContext = MODES.EMERGENCY;
        if (targetContext === 'default') targetContext = null;
        if (targetContext !== MODES.EMERGENCY && targetContext !== MODES.RECOVERY && targetContext !== MODES.UNCLEAR) {
            targetContext = null;
        }

        const prevContext = activeContext;
        activeContext = targetContext;
        if (targetContext !== MODES.UNCLEAR) {
            activeSharedTool = null;
            try {
                sessionStorage.removeItem('tempo_active_shared_tool');
            } catch (e) {}
        }

        // Establish sourceContext according to new activeContext
        if (targetContext === MODES.UNCLEAR) {
            const origin = options.sourceContext || (prevContext === MODES.EMERGENCY ? 'emergency' : (prevContext === MODES.RECOVERY ? 'recovery' : (getOriginatingMode() || 'entry')));
            setOriginatingMode(origin);
            sourceContext = origin;
        } else {
            sourceContext = targetContext === MODES.EMERGENCY ? 'emergency' : (targetContext === MODES.RECOVERY ? 'recovery' : 'entry');
            clearOriginatingMode();
        }

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

        if (targetContext !== MODES.RECOVERY) {
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
            } else if (targetContext === MODES.UNCLEAR) {
                window.TempoApp.showToast("🧭 Switched to Unclear Mode");
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
            if (!options.skipSetupCheck && window.TempoRecoverySetup && typeof window.TempoRecoverySetup.handleRmodeEntry === 'function') {
                window.TempoRecoverySetup.handleRmodeEntry(options);
            } else if (!options.skipSetupCheck && window.TempoRecoverySetup && typeof window.TempoRecoverySetup.shouldShowFirstTimeWelcome === 'function') {
                if (window.TempoRecoverySetup.shouldShowFirstTimeWelcome()) {
                    window.TempoRecoverySetup.open(1);
                }
            }
        }
    }"""

replacement3 = """    function transitionContext(targetContext, options = {}) {
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
    }"""

assert target3 in content, 'target3 not found in mode.js'
content = content.replace(target3, replacement3, 1)

# 4. Update returnToSourceContext, resolveActiveDashboardContext, navigateToActiveDashboard, and requestMode
target4 = """    /**
     * Returns to the source context dashboard from which a tool/assessment was opened.
     */
    function returnToSourceContext() {
        activeSharedTool = null;

        document.body.style.backgroundColor = '';
        const mainEl = document.querySelector('main');
        if (mainEl) mainEl.style.backgroundColor = '';

        const scScreen = document.getElementById('screen-stress-check');
        if (scScreen) scScreen.classList.add('hidden');

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
            clearOriginatingMode();
            transitionContext(null, { silent: true });
            if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
                window.TempoApp.navigateTo('today');
            }
            return;
        }

        // Authenticated user resolution:
        // Priority order:
        // 1. sourceContext or getOriginatingMode() if it points to an active context (recovery/emergency/unclear)
        // 2. activeContext if it points to an active context
        // 3. Persisted user active context (from getUserPersistedActiveContext())
        // 4. Default / Entry Home only if user has no saved active context
        const origin = sourceContext || getOriginatingMode();
        clearOriginatingMode();
        sourceContext = null;

        let target = null;
        if (origin === 'emergency' || origin === 'recovery' || origin === 'unclear') {
            target = origin;
        } else if (activeContext === MODES.EMERGENCY || activeContext === MODES.RECOVERY || activeContext === MODES.UNCLEAR) {
            target = activeContext;
        } else {
            const persisted = getUserPersistedActiveContext();
            if (persisted === MODES.EMERGENCY || persisted === MODES.RECOVERY || persisted === MODES.UNCLEAR) {
                target = persisted;
            } else {
                target = null;
            }
        }

        if (target === MODES.EMERGENCY || target === 'emergency') {
            transitionContext(MODES.EMERGENCY, { silent: true });
        } else if (target === MODES.RECOVERY || target === 'recovery') {
            transitionContext(MODES.RECOVERY, { silent: true });
        } else if (target === MODES.UNCLEAR || target === 'unclear') {
            transitionContext(MODES.UNCLEAR, { silent: true });
        } else {
            transitionContext(null, { silent: true });
        }
        if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
            window.TempoApp.navigateTo('today');
        }
        if (typeof renderShellIndicator === 'function') {
            renderShellIndicator();
        }
        if (typeof refreshStreakCardIfPresent === 'function') {
            refreshStreakCardIfPresent();
        }
    }

    /**
     * Resolves the canonical dashboard context associated with the user's active context.
     * Preserves originating mode when inside a shared assessment/tool flow like Ucheck.
     */
    function resolveActiveDashboardContext() {
        // 1. If currently in Ucheck or shared tool, resolve originating mode first
        const origin = getOriginatingMode();
        if (origin === 'recovery') return MODES.RECOVERY;
        if (origin === 'emergency') return MODES.EMERGENCY;
        if (origin === 'unclear') return MODES.UNCLEAR;

        if (activeSharedTool === 'strack' || activeSharedTool === 'wplan') {
            if (sourceContext === 'recovery') return MODES.RECOVERY;
            if (sourceContext === 'emergency') return MODES.EMERGENCY;
            if (sourceContext === 'unclear') return MODES.UNCLEAR;
        }

        // 2. Check activeContext in memory
        if (activeContext === MODES.EMERGENCY) return MODES.EMERGENCY;
        if (activeContext === MODES.RECOVERY) return MODES.RECOVERY;
        if (activeContext === MODES.UNCLEAR) return MODES.UNCLEAR;

        // 3. Check established context in localStorage for authenticated user
        const persisted = getUserPersistedActiveContext();
        if (persisted === MODES.EMERGENCY) return MODES.EMERGENCY;
        if (persisted === MODES.RECOVERY) return MODES.RECOVERY;
        if (persisted === MODES.UNCLEAR) return MODES.UNCLEAR;

        // 4. Fallback to origin or sourceContext if entry
        if (origin === 'entry' || sourceContext === 'entry') return MODES.DEFAULT;

        // 5. Safe fallback to default Entry Home
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
            transitionContext(MODES.EMERGENCY, { silent: true });
        } else if (dest === MODES.RECOVERY) {
            transitionContext(MODES.RECOVERY, { silent: true });
        } else if (dest === MODES.UNCLEAR) {
            transitionContext(MODES.UNCLEAR, { silent: true });
            if (window.TempoUnclearMode && typeof window.TempoUnclearMode.renderHome === 'function') {
                window.TempoUnclearMode.renderHome();
            }
        } else {
            transitionContext(null, { silent: true });
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
            setOriginatingMode(origin);
            transitionContext(MODES.UNCLEAR, { sourceContext: origin });
            if (window.TempoUnclearMode && typeof window.TempoUnclearMode.renderHome === 'function') {
                window.TempoUnclearMode.renderHome();
            }
            if (window.TempoApp) window.TempoApp.navigateTo('today');
            return;
        }"""

replacement4 = """    /**
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
        }"""

assert target4 in content, 'target4 not found in mode.js'
content = content.replace(target4, replacement4, 1)

# 5. Update setMode
target5 = """        if (newMode === MODES.UNCLEAR) {
            const origin = options.sourceContext || (activeContext === MODES.EMERGENCY ? 'emergency' : (activeContext === MODES.RECOVERY ? 'recovery' : (getOriginatingMode() || 'entry')));
            setOriginatingMode(origin);
            transitionContext(MODES.UNCLEAR, Object.assign({}, options, { sourceContext: origin }));
            if (window.TempoUnclearMode && typeof window.TempoUnclearMode.renderHome === 'function') {
                window.TempoUnclearMode.renderHome();
            }
            if (window.TempoApp) window.TempoApp.navigateTo('today');
            return;
        }"""

replacement5 = """        if (newMode === MODES.UNCLEAR) {
            const origin = options.sourceContext || (activeContext === MODES.EMERGENCY ? 'emergency' : (activeContext === MODES.RECOVERY ? 'recovery' : (getOriginatingMode() || 'entry')));
            openUcheck(Object.assign({}, options, { sourceContext: origin }));
            return;
        }"""

assert target5 in content, 'target5 not found in mode.js'
content = content.replace(target5, replacement5, 1)

# Ensure strictly lone-LF
content = content.replace('\r\n', '\n').replace('\r', '\n')

with open('mode.js', 'wb') as f:
    f.write(content.encode('utf-8'))

print('Successfully updated mode.js')
