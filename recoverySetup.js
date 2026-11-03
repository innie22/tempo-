/**
 * TEMPO WELLBEING — RECOVERY MODE: RECOVERY ENTRY & SETUP FLOW (PHASE 3)
 * File: recoverySetup.js
 *
 * Architecture:
 * 1. First-time Recovery entry check (Welcome -> Setup or direct Home entry)
 * 2. 7-Stage Calm Recovery Setup Flow:
 *    Stage 1: Welcome ("Start my recovery check-in" vs "I'll explore first")
 *    Stage 2: Looking Back (Mind, Body, Behavior, Emotions chips + custom)
 *    Stage 3: What Helped (Body, Rest, Support, Boundaries chips + custom)
 *    Stage 4: Recovery Note (Warning signs, Helpers, Reminders, Support contacts)
 *    Stage 5: Build My Self-check (Reuses Phase 2 tracker system with reflection suggestions)
 *    Stage 6: First Self-check (Reuses Phase 2 Daily Check-in form & streak engine)
 *    Stage 7: Recovery Check-in Complete + Contextual Academic Next Step
 * 3. Draft preservation across stages & navigation
 * 4. Absolute rule: NEVER creates a "Recovery Plan" entity.
 */

(function () {
    'use strict';

    // =========================================================================
    // REFLECTION SUGGESTIONS DATA (STAGES 2 & 3)
    // =========================================================================

    const LOOKING_BACK_GROUPS = [
        {
            category: 'mind',
            label: 'Mind',
            items: [
                'Trouble focusing',
                'Thoughts kept racing',
                'Hard to switch off',
                'Felt mentally overloaded'
            ]
        },
        {
            category: 'body',
            label: 'Body',
            items: [
                'Felt tired',
                'Trouble sleeping',
                'Tension',
                'Low energy'
            ]
        },
        {
            category: 'behavior',
            label: 'Behavior',
            items: [
                'Put things off',
                'Worked for too long without stopping',
                'Stayed up later than usual',
                'Pulled away from things I normally do'
            ]
        },
        {
            category: 'emotions',
            label: 'Emotions',
            items: [
                'Felt overwhelmed',
                'Felt irritable',
                'Felt anxious',
                'Felt emotionally drained'
            ]
        }
    ];

    const WHAT_HELPED_GROUPS = [
        {
            category: 'body',
            label: 'Body',
            items: [
                'Eating something',
                'Drinking water',
                'Going outside',
                'Moving around for a while'
            ]
        },
        {
            category: 'rest',
            label: 'Rest',
            items: [
                'Taking a real break',
                'Sleeping',
                'Doing something unrelated to work',
                'Spending time somewhere quiet'
            ]
        },
        {
            category: 'support',
            label: 'Support',
            items: [
                'Talking to someone I trust',
                'Being around other people',
                'Asking someone for help'
            ]
        },
        {
            category: 'boundaries',
            label: 'Boundaries',
            items: [
                'Stopping work for the day',
                'Saying no to something',
                'Reducing what I was trying to finish',
                'Giving myself more time'
            ]
        }
    ];

    const GENTLE_REMINDER_SUGGESTIONS = [
        "I don't have to solve everything at once.",
        "Taking a real break is allowed.",
        "One next step is enough.",
        "I can slow things down before deciding what comes next."
    ];

    // =========================================================================
    // STATE & PERSISTENCE
    // =========================================================================

    function getUserId() {
        if (window.TempoAuth && typeof window.TempoAuth.getCurrentUserId === 'function') {
            const uid = window.TempoAuth.getCurrentUserId();
            if (uid) return uid;
        }
        return 'local_user';
    }

    function isViLocale() {
        if (window.TempoI18n && typeof window.TempoI18n.getLanguage === 'function') {
            return window.TempoI18n.getLanguage() === 'vi';
        }
        try {
            const stored = localStorage.getItem('tempo_language') || localStorage.getItem('tempo_lang');
            if (stored === 'vi' || stored === 'en') return stored === 'vi';
        } catch (e) {}
        return false;
    }

    function t(path, params = {}, fallback = '') {
        if (typeof params === 'string') {
            fallback = params;
            params = {};
        }
        if (typeof window.t === 'function') {
            const res = window.t(path, params, fallback);
            if (res) return res;
        }
        return fallback || '';
    }

    function isIntroSeen() {
        const uid = getUserId();
        return localStorage.getItem(`tempo_recovery_intro_seen_${uid}`) === 'true';
    }

    function markIntroSeen() {
        const uid = getUserId();
        localStorage.setItem(`tempo_recovery_intro_seen_${uid}`, 'true');
    }

    function isSetupCompleted() {
        const uid = getUserId();
        return localStorage.getItem(`tempo_recovery_setup_status_${uid}`) === 'completed';
    }

    function markSetupCompleted() {
        const uid = getUserId();
        localStorage.setItem(`tempo_recovery_setup_status_${uid}`, 'completed');
        markIntroSeen();
    }

    function resetSetupState() {
        const uid = getUserId();
        localStorage.removeItem(`tempo_recovery_setup_status_${uid}`);
        localStorage.removeItem(`tempo_recovery_intro_seen_${uid}`);
        localStorage.removeItem(`tempo_recovery_setup_draft_${uid}`);
        try {
            sessionStorage.removeItem(`tempo_rmode_session_welcomed_${uid}`);
            sessionStorage.removeItem(`tempo_recovery_setup_open_${uid}`);
        } catch (e) {}
    }

    /**
     * Determines the user's tracking status based on ACTUAL saved tracking items and history.
     * Edge case handling:
     * - Graceful fallback on loading/database error: defaults safely to returning user so data is never wiped.
     * - Recognizes users with tracking history even if active trackers were archived.
     */
    function checkUserTrackingStatus() {
        try {
            const uid = getUserId();
            let activeTrackers = [];
            let allTrackers = [];
            let checkins = [];
            let setups = [];

            if (window.TempoRecoverySelfCheck) {
                if (typeof window.TempoRecoverySelfCheck.getActiveTrackers === 'function') {
                    activeTrackers = window.TempoRecoverySelfCheck.getActiveTrackers() || [];
                }
                if (typeof window.TempoRecoverySelfCheck.getTrackers === 'function') {
                    allTrackers = window.TempoRecoverySelfCheck.getTrackers(true) || [];
                }
                if (typeof window.TempoRecoverySelfCheck.getDailyCheckins === 'function') {
                    checkins = window.TempoRecoverySelfCheck.getDailyCheckins() || [];
                }
                if (typeof window.TempoRecoverySelfCheck.getSetups === 'function') {
                    setups = window.TempoRecoverySelfCheck.getSetups() || [];
                }
            }

            // Fallback: direct localStorage inspection for robustness
            if (allTrackers.length === 0) {
                try {
                    const raw = localStorage.getItem(`tempo_selfcheck_trackers_${uid}`) || (uid === 'local_user' ? localStorage.getItem('tempo_selfcheck_trackers') : null);
                    if (raw) {
                        const parsed = JSON.parse(raw);
                        if (Array.isArray(parsed) && parsed.length > 0) {
                            allTrackers = parsed;
                            activeTrackers = parsed.filter(t => !t.is_archived);
                        }
                    }
                } catch (e) {}
            }

            if (checkins.length === 0) {
                try {
                    const raw = localStorage.getItem(`tempo_selfcheck_checkins_${uid}`) || (uid === 'local_user' ? localStorage.getItem('tempo_selfcheck_checkins') : null);
                    if (raw) {
                        const parsed = JSON.parse(raw);
                        if (Array.isArray(parsed) && parsed.length > 0) {
                            checkins = parsed;
                        }
                    }
                } catch (e) {}
            }

            if (setups.length === 0) {
                try {
                    const raw = localStorage.getItem(`tempo_recovery_setups_${uid}`) || localStorage.getItem(`tempo_selfcheck_setups_${uid}`);
                    if (raw) {
                        const parsed = JSON.parse(raw);
                        if (Array.isArray(parsed) && parsed.length > 0) {
                            setups = parsed;
                        }
                    }
                } catch (e) {}
            }

            const hasActive = activeTrackers.length > 0;
            const hasHistory = allTrackers.length > 0 || checkins.length > 0 || setups.length > 0;
            const isReturning = hasActive || hasHistory;

            return {
                isReturning,
                hasActive,
                hasHistory,
                activeTrackers,
                allTrackers,
                activeCount: activeTrackers.length,
                checkinsCount: checkins.length
            };
        } catch (err) {
            console.error("[TempoRecoverySetup] checkUserTrackingStatus error (defaulting to returning user):", err);
            return {
                isReturning: true,
                hasActive: false,
                hasHistory: true,
                activeTrackers: [],
                allTrackers: [],
                activeCount: 0,
                checkinsCount: 0
            };
        }
    }

    // In-memory setup session draft
    let setupDraft = {
        currentStage: 1,
        lookingBackSelections: [], // array of string names
        lookingBackCustom: [],
        whatHelpedSelections: [], // array of string names
        whatHelpedCustom: [],
        noteWarningSigns: [],
        noteHelpers: [],
        noteReminders: [],
        noteSupportPeople: [],
        selectedTrackerIds: []
    };

    function saveDraftToStorage() {
        try {
            const uid = getUserId();
            localStorage.setItem(`tempo_recovery_setup_draft_${uid}`, JSON.stringify(setupDraft));
        } catch (e) {}
    }

    function loadDraftFromStorage() {
        try {
            const uid = getUserId();
            const raw = localStorage.getItem(`tempo_recovery_setup_draft_${uid}`);
            if (raw) {
                const parsed = JSON.parse(raw);
                setupDraft = { ...setupDraft, ...parsed };
                if (!Array.isArray(setupDraft.selectedTrackerIds)) {
                    setupDraft.selectedTrackerIds = [];
                }
            }
        } catch (e) {}
    }

    function hasCompletedRmodeSetup(optionalUid) {
        const uid = optionalUid || getUserId();
        if (!uid) return false;

        // 1. Explicit account-scoped setup completion status
        try {
            const status = localStorage.getItem(`tempo_recovery_setup_status_${uid}`);
            if (status === 'completed') return true;
        } catch (e) {}

        // 2. Persisted setups for this account
        try {
            const rawSetups = localStorage.getItem(`tempo_recovery_setups_${uid}`) || localStorage.getItem(`tempo_selfcheck_setups_${uid}`);
            if (rawSetups) {
                const parsed = JSON.parse(rawSetups);
                if (Array.isArray(parsed) && parsed.length > 0) return true;
            }
        } catch (e) {}

        return false;
    }

    // Determine if first-time Recovery visitor based on actual Tracking System data
    function shouldShowFirstTimeWelcome() {
        const status = checkUserTrackingStatus();
        return !status.isReturning;
    }

    // =========================================================================
    // MODAL SHELL & NAVIGATION
    // =========================================================================

    function ensureModalMounted() {
        if (document.getElementById('modal-recovery-setup')) return;

        const modal = document.createElement('div');
        modal.id = 'modal-recovery-setup';
        modal.className = 'fixed inset-0 z-50 flex items-center justify-center modal-backdrop p-3 sm:p-4 hidden';
        modal.setAttribute('role', 'dialog');
        modal.setAttribute('aria-modal', 'true');
        modal.innerHTML = `
            <div class="tempo-card max-w-2xl w-full p-6 sm:p-8 space-y-6 bg-white rounded-3xl shadow-2xl relative border border-[#EAE4DF] max-h-[92vh] overflow-y-auto">
                <button type="button" onclick="window.TempoRecoverySetup.handleModalClose()"
                        class="absolute top-5 right-5 text-gray-400 hover:text-gray-700 text-lg transition cursor-pointer" title="Close">✕</button>
                <div id="recovery-setup-stage-container"></div>
            </div>
        `;

        // Outside-click dismissal for modal-recovery-setup backdrop
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                handleModalClose();
            }
        });

        document.body.appendChild(containerPlanConfirmModal());
        document.body.appendChild(modal);
    }

    function handleModalClose() {
        if (setupDraft && (setupDraft.currentStage === 'case1_welcome' || setupDraft.currentStage === 1)) {
            handleCase1Later();
        } else if (setupDraft && (setupDraft.currentStage === 'case2_welcome' || setupDraft.currentStage === 'case2_review' || setupDraft.currentStage === 'returning_welcome' || setupDraft.currentStage === 'review_system')) {
            handleCase2GoToDashboard();
        } else {
            close();
            if (window.TempoMode && typeof window.TempoMode.renderRmodeHome === 'function') {
                window.TempoMode.renderRmodeHome();
            }
        }
    }

    function containerPlanConfirmModal() {
        const el = document.createElement('div');
        el.id = 'modal-recovery-plan-confirm';
        el.className = 'fixed inset-0 z-[60] flex items-center justify-center modal-backdrop p-4 hidden';
        el.innerHTML = `
            <div class="tempo-card max-w-md w-full p-6 space-y-5 bg-white rounded-3xl shadow-2xl relative border border-[#FFD2BA]">
                <div class="space-y-1 text-center">
                    <span class="text-[11px] font-extrabold uppercase tracking-wider text-[#FF6B2C]">CREATE A PLAN</span>
                    <h3 class="font-heading text-xl font-extrabold text-[#202124]">Switch to Urgent Mode?</h3>
                    <p class="text-xs text-[#6F6B68] leading-relaxed">
                        Tempo's Urgent Plan helps when several tasks or deadlines need sorting out. Would you like to switch to Urgent Mode and create one?
                    </p>
                </div>
                <div class="pt-2 flex flex-col sm:flex-row items-center justify-center gap-2.5">
                    <button type="button" onclick="window.TempoRecoverySetup.confirmSwitchToUrgentPlan()"
                            class="btn-primary w-full sm:w-auto px-5 py-2.5 rounded-xl font-bold text-xs sm:text-sm shadow-xs transition cursor-pointer">
                        Switch & create a plan →
                    </button>
                    <button type="button" onclick="window.TempoRecoverySetup.closePlanConfirmModal()"
                            class="w-full sm:w-auto px-4 py-2.5 rounded-xl text-xs font-semibold text-[#6F6B68] hover:text-[#202124] transition cursor-pointer">
                        Not now
                    </button>
                </div>
            </div>
        `;
        return el;
    }

    function isReturningUser() {
        return checkUserTrackingStatus().isReturning;
    }

    /**
     * Entry handler triggered when switching to Rmode.
     * Prevents duplicate modals if already welcomed in the current session.
     */
    function handleRmodeEntry(options = {}) {
        const uid = getUserId();
        const sessionKey = `tempo_rmode_session_welcomed_${uid}`;
        const isSessionWelcomed = sessionStorage.getItem(sessionKey) === 'true';

        if (!options.force && isSessionWelcomed) {
            return;
        }

        // Set session guard to prevent duplicate modals within same Rmode session
        sessionStorage.setItem(sessionKey, 'true');

        const status = checkUserTrackingStatus();
        if (status.isReturning) {
            open('case2_welcome', options);
        } else {
            open('case1_welcome', options);
        }
    }

    function open(stage = null, options = {}) {
        ensureModalMounted();
        loadDraftFromStorage();

        let targetStage = stage;
        if (!targetStage || targetStage === 1 || targetStage === 'auto') {
            const status = checkUserTrackingStatus();
            targetStage = status.isReturning ? 'case2_welcome' : 'case1_welcome';
        }

        goToStage(targetStage);

        const modal = document.getElementById('modal-recovery-setup');
        if (modal) {
            modal.classList.remove('hidden');
            document.body.classList.add('overflow-hidden');
            try {
                const uid = getUserId();
                sessionStorage.setItem(`tempo_recovery_setup_open_${uid}`, 'true');
            } catch (e) {}
        }
    }

    function updateRecoveryCardTheme(isWarmTheme) {
        const modal = document.getElementById('modal-recovery-setup');
        if (!modal) return;
        const card = modal.querySelector('.tempo-card');
        const closeBtn = modal.querySelector('button[title="Close"]');
        if (!card) return;

        if (isWarmTheme) {
            // Updated palette: soft Warm Blush tint background (not pure-white!), subtle Warm Blush border
            card.style.backgroundColor = '#FAF4F0';
            card.style.borderColor = '#ECC9BA';
            card.setAttribute('data-tempo-theme', 'warm-blush');
            if (closeBtn) {
                closeBtn.className = 'absolute top-5 right-5 text-[#6F6B68] hover:text-[#202124] hover:bg-[#ECC9BA]/40 p-2 rounded-xl text-lg transition cursor-pointer';
            }
        } else {
            // Restore default styles for other stages
            card.style.backgroundColor = '';
            card.style.borderColor = '';
            card.removeAttribute('data-tempo-theme');
            if (closeBtn) {
                closeBtn.className = 'absolute top-5 right-5 text-gray-400 hover:text-gray-700 text-lg transition cursor-pointer';
            }
        }
    }

    function close() {
        updateRecoveryCardTheme(false);
        const modal = document.getElementById('modal-recovery-setup');
        if (modal) modal.classList.add('hidden');
        document.body.classList.remove('overflow-hidden');
        try {
            const uid = getUserId();
            sessionStorage.removeItem(`tempo_recovery_setup_open_${uid}`);
        } catch (e) {}
    }

    function exploreFirst() {
        handleCase1Later();
    }

    function goToStage(stageNum) {
        setupDraft.currentStage = stageNum;
        saveDraftToStorage();

        const isWarmStage = (stageNum === 'case2_welcome' || stageNum === 'returning_welcome' || stageNum === 'case2_review' || stageNum === 'review_system' || stageNum === 'adjust_trackers' || stageNum === 'adjust_note' || stageNum === 'adjust_review');
        updateRecoveryCardTheme(isWarmStage);

        const container = document.getElementById('recovery-setup-stage-container');
        if (!container) return;

        if (stageNum === 'case1_welcome' || stageNum === 1) renderCase1Welcome(container);
        else if (stageNum === 'case2_welcome' || stageNum === 'returning_welcome') renderCase2Welcome(container);
        else if (stageNum === 'case2_review' || stageNum === 'review_system') renderCase2ReviewSystem(container);
        else if (stageNum === 'hub') renderReturningHub(container);
        else if (stageNum === 'confirm_new_setup') renderCreateNewSetupConfirm(container);
        else if (stageNum === 'adjust_trackers') renderStageAdjustTrackers(container);
        else if (stageNum === 'adjust_note') renderStageAdjustNote(container);
        else if (stageNum === 'adjust_review') renderStageAdjustReview(container);
        else if (stageNum === 2) renderStage2LookingBack(container);
        else if (stageNum === 3) renderStage3WhatHelped(container);
        else if (stageNum === 4) renderStage4RecoveryNote(container);
        else if (stageNum === 5) renderStage5BuildSelfCheck(container);
        else if (stageNum === 6) renderStage6FirstSelfCheck(container);
        else if (stageNum === 7) renderStage7Complete(container);
    }

    // =========================================================================
    // =========================================================================
    // RETURNING USER SETUP HUB & ADJUSTMENT FLOW (PHASE 3B)
    // =========================================================================

    let adjustmentDraft = {
        trackers: [],
        newTrackers: [],
        noteItems: [],
        editingTrackerIndex: null,
        editingIsNew: false
    };

    function startAdjustmentFlow() {
        const activeTrackers = (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.getActiveTrackers === 'function')
            ? window.TempoRecoverySelfCheck.getActiveTrackers()
            : [];

        adjustmentDraft.trackers = activeTrackers.map(t => ({
            ...t,
            isKept: true,
            originalMethod: t.check_method,
            originalName: t.name,
            originalUnit: t.quantity_unit || '',
            wasEdited: false
        }));

        adjustmentDraft.newTrackers = [];
        adjustmentDraft.editingTrackerIndex = null;
        adjustmentDraft.editingIsNew = false;

        const noteItems = (window.TempoRecoveryNote && typeof window.TempoRecoveryNote.getItems === 'function')
            ? window.TempoRecoveryNote.getItems()
            : [];
        adjustmentDraft.noteItems = noteItems.map(item => ({ ...item }));

        goToStage('adjust_trackers');
    }

    function promptCreateNewSetup() {
        goToStage('confirm_new_setup');
    }

    function confirmCreateNewSetup() {
        if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.archiveCurrentSetup === 'function') {
            window.TempoRecoverySelfCheck.archiveCurrentSetup();
        }

        // Reset setup draft for fresh start
        setupDraft = {
            currentStage: 1,
            lookingBackSelections: [],
            lookingBackCustom: [],
            whatHelpedSelections: [],
            whatHelpedCustom: [],
            noteWarningSigns: [],
            noteHelpers: [],
            noteReminders: [],
            noteSupportPeople: [],
            selectedTrackerIds: []
        };
        saveDraftToStorage();

        const uid = getUserId();
        localStorage.removeItem(`tempo_recovery_setup_status_${uid}`);

        if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
            window.TempoApp.showToast("Current setup archived safely. Starting your new setup.");
        }

        goToStage(1);
    }

    function renderReturningHub(container) {
        const activeTrackers = (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.getActiveTrackers === 'function')
            ? window.TempoRecoverySelfCheck.getActiveTrackers()
            : [];

        container.innerHTML = `
            <div class="space-y-6 py-2">
                <div class="space-y-2 text-center max-w-lg mx-auto">
                    <div class="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-[#EDF7F1] text-[#166545] border border-[#CDE9DA] text-xs font-extrabold uppercase tracking-wider">
                        <span>🌱</span>
                        <span>RECOVERY MODE · SETUP</span>
                    </div>
                    <h2 class="font-heading text-2xl sm:text-3xl font-extrabold text-[#202124] tracking-tight">
                        Setup Management
                    </h2>
                    <p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed">
                        You're currently tracking ${activeTrackers.length} item${activeTrackers.length === 1 ? '' : 's'}. You can adjust your active setup or start fresh with a new setup.
                    </p>
                </div>

                <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                    <!-- Option 1: Adjust My Current Setup -->
                    <div class="p-5 rounded-2xl bg-white border-2 border-[#CDE9DA] hover:border-[#166545] transition-all shadow-xs flex flex-col justify-between space-y-4">
                        <div class="space-y-2">
                            <div class="w-10 h-10 rounded-xl bg-[#EDF7F1] text-[#166545] flex items-center justify-center text-lg font-bold">
                                ⚙️
                            </div>
                            <h3 class="font-heading text-lg font-bold text-[#202124]">Adjust my current setup</h3>
                            <p class="text-xs text-[#6F6B68] leading-relaxed">
                                Keep or stop items, change tracking methods (effective today), edit names and units, add new trackers, and review your Recovery Notice. All past records remain completely safe.
                            </p>
                        </div>
                        <button type="button" onclick="window.TempoRecoverySetup.startAdjustmentFlow()"
                                class="btn-primary w-full py-2.5 rounded-xl font-bold text-xs sm:text-sm shadow-xs transition cursor-pointer">
                            Adjust current setup →
                        </button>
                    </div>

                    <!-- Option 2: Create a New Setup -->
                    <div class="p-5 rounded-2xl bg-white border border-stone-200 hover:border-stone-400 transition-all shadow-xs flex flex-col justify-between space-y-4">
                        <div class="space-y-2">
                            <div class="w-10 h-10 rounded-xl bg-stone-100 text-stone-700 flex items-center justify-center text-lg font-bold">
                                📦
                            </div>
                            <h3 class="font-heading text-lg font-bold text-[#202124]">Create a new setup</h3>
                            <p class="text-xs text-[#6F6B68] leading-relaxed">
                                Safely archive your current setup and its check-in history. Start completely fresh through the calm setup flow without losing your past records in storage.
                            </p>
                        </div>
                        <button type="button" onclick="window.TempoRecoverySetup.promptCreateNewSetup()"
                                class="w-full py-2.5 rounded-xl font-bold text-xs sm:text-sm bg-stone-100 hover:bg-stone-200 text-stone-800 transition cursor-pointer">
                            Create a new setup →
                        </button>
                    </div>
                </div>

                <div class="pt-2 text-center">
                    <button type="button" onclick="window.TempoRecoverySetup.close()"
                            class="text-xs font-semibold text-stone-500 hover:text-stone-800 transition cursor-pointer">
                        Return to Dashboard
                    </button>
                </div>
            </div>
        `;
    }

    function renderCreateNewSetupConfirm(container) {
        const activeTrackers = (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.getActiveTrackers === 'function')
            ? window.TempoRecoverySelfCheck.getActiveTrackers()
            : [];

        container.innerHTML = `
            <div class="space-y-6 py-4 max-w-lg mx-auto text-center">
                <div class="w-12 h-12 rounded-2xl bg-[#FFE9DC] text-[#B83D08] border border-[#FFD2BA] flex items-center justify-center text-2xl font-bold mx-auto">
                    📦
                </div>

                <div class="space-y-2">
                    <span class="text-[11px] font-extrabold uppercase tracking-wider text-[#B83D08]">CONFIRM NEW SETUP</span>
                    <h2 class="font-heading text-2xl font-extrabold text-[#202124]">Archive Current Setup & Start Fresh?</h2>
                    <p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed">
                        Your ${activeTrackers.length} active tracking item${activeTrackers.length === 1 ? '' : 's'} and all past check-in records will be <strong>safely preserved in your archive</strong>.
                    </p>
                    <p class="text-xs text-[#6F6B68] leading-relaxed bg-[#FBF9F6] p-3 rounded-xl border border-stone-200">
                        They will no longer appear in your active daily check-in flow, but will never be deleted. You will then be guided through the calm setup flow to select fresh tracking items.
                    </p>
                </div>

                <div class="pt-2 flex flex-col sm:flex-row items-center justify-center gap-3">
                    <button type="button" onclick="window.TempoRecoverySetup.confirmCreateNewSetup()"
                            class="btn-primary w-full sm:w-auto px-6 py-2.5 rounded-xl font-bold text-xs sm:text-sm shadow-xs transition cursor-pointer bg-[#B83D08] hover:bg-[#9E3406] border-none text-white">
                        Archive & start new setup →
                    </button>
                    <button type="button" onclick="window.TempoRecoverySetup.goToStage('hub')"
                            class="w-full sm:w-auto px-5 py-2.5 rounded-xl text-xs font-semibold text-stone-600 hover:text-stone-900 transition cursor-pointer">
                        Cancel
                    </button>
                </div>
            </div>
        `;
    }

    // =========================================================================
    // ADJUSTMENT STAGE 1: TRACKERS REVIEW & EDITING
    // =========================================================================

    function toggleTrackerKept(idx) {
        if (adjustmentDraft.trackers[idx]) {
            adjustmentDraft.trackers[idx].isKept = !adjustmentDraft.trackers[idx].isKept;
            renderStageAdjustTrackers(document.getElementById('recovery-setup-stage-container'));
        }
    }

    function removeNewTracker(idx) {
        if (adjustmentDraft.newTrackers[idx]) {
            adjustmentDraft.newTrackers.splice(idx, 1);
            renderStageAdjustTrackers(document.getElementById('recovery-setup-stage-container'));
        }
    }

    function openEditTrackerInAdjustment(idx, isNew = false) {
        const target = isNew ? adjustmentDraft.newTrackers[idx] : adjustmentDraft.trackers[idx];
        if (!target) return;
        if (window.TempoSelfCheckWorkspace && typeof window.TempoSelfCheckWorkspace.openAdjustTracker === 'function') {
            window.TempoSelfCheckWorkspace.openAdjustTracker(target.id ? target.id : target);
        } else if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.openTrackerModal === 'function') {
            window.TempoRecoverySelfCheck.openTrackerModal(target.id ? target.id : target);
        }
    }

    function closeTrackerEditInAdjustment() {
        if (window.TempoSelfCheckWorkspace && typeof window.TempoSelfCheckWorkspace.closeAdjustModal === 'function') {
            window.TempoSelfCheckWorkspace.closeAdjustModal();
        }
    }

    function saveTrackerEditInAdjustment(idx, isNew) {
        if (window.TempoSelfCheckWorkspace && typeof window.TempoSelfCheckWorkspace.saveAdjustTracker === 'function') {
            window.TempoSelfCheckWorkspace.saveAdjustTracker();
        }
    }

    function openAddTrackerInAdjustment() {
        if (window.TempoSelfCheckWorkspace && typeof window.TempoSelfCheckWorkspace.openAddTracking === 'function') {
            window.TempoSelfCheckWorkspace.openAddTracking();
        } else if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.openTrackerModal === 'function') {
            window.TempoRecoverySelfCheck.openTrackerModal();
        }
    }

    function promptAddNewTrackerInAdjustment() {
        openAddTrackerInAdjustment();
    }

    function handleAdjustBack() {
        handleCase2GoToDashboard();
    }

    function renderStageAdjustTrackers(container) {
        const isVi = isViLocale();
        updateRecoveryCardTheme(true);

        const stepBadge = t('modes.recovery.onboarding.adjustStep1Badge', {}, isVi ? 'BƯỚC 1/3 · HỆ THỐNG TRACKING' : 'STEP 1 OF 3 · TRACKING SYSTEM');
        const setupAdjustmentLabel = t('modes.recovery.onboarding.adjustStep1Tag', {}, isVi ? 'Thiết lập điều chỉnh' : 'Setup Adjustment');
        const title = t('modes.recovery.onboarding.adjustStep1Title', {}, isVi ? 'Điều chỉnh các mục tracking' : 'Adjust your tracking items');
        const desc = t('modes.recovery.onboarding.adjustStep1Desc', {}, isVi ? 'Chọn các mục bạn muốn giữ lại, thay đổi cách tracking hoặc ngừng tracking. Các mục đã ngừng sẽ được lưu trữ và dữ liệu trước đó vẫn được giữ nguyên.' : 'Choose which items to keep, update tracking methods, or stop tracking items. Stopped items are archived and past data is preserved.');

        const editLabel = t('modes.recovery.onboarding.adjustEditBtn', {}, isVi ? 'Chỉnh sửa' : 'Edit');
        const stopLabel = t('modes.recovery.onboarding.adjustStopBtn', {}, isVi ? 'Ngừng tracking' : 'Stop tracking');
        const keepLabel = t('modes.recovery.onboarding.adjustKeepBtn', {}, isVi ? 'Tiếp tục tracking' : 'Keep tracking');
        const addLabel = t('modes.recovery.onboarding.adjustAddBtn', {}, isVi ? '+ Thêm mục tracking mới' : '+ Add new tracking item');
        const backLabel = t('modes.recovery.onboarding.adjustBackBtn', {}, isVi ? '← Quay lại Dashboard' : '← Back to Hub');
        const continueLabel = t('modes.recovery.onboarding.adjustContinueBtn', {}, isVi ? 'Tiếp tục đến Lời nhắn phục hồi →' : 'Continue to Recovery Notice →');
        const activeLabel = t('modes.recovery.onboarding.adjustActiveBadge', {}, isVi ? 'Đang tracking' : 'Active');

        const trackersListHTML = adjustmentDraft.trackers.map((t, idx) => {
            const dotColor = t.type_color || (t.category === 'stress_sign' ? '#D48366' : (t.category === 'supportive' ? '#8EA28F' : '#93AFBC'));
            const isKept = t.isKept !== false;
            const methodChanged = t.wasEdited && t.check_method !== t.originalMethod;

            let methodDesc = t.check_method;
            if (t.check_method === 'percentage') {
                methodDesc = isVi ? 'Phần trăm (%)' : 'Percentage (%)';
            } else if (t.check_method === 'quantity') {
                const rawUnit = t.quantity_unit || '';
                if (isVi) {
                    const unitStr = (rawUnit === 'min' || rawUnit === 'minutes' || rawUnit === 'phút' || !rawUnit) ? 'phút' : rawUnit;
                    methodDesc = `Thời lượng (${unitStr})`;
                } else {
                    const unitStr = (rawUnit === 'phút' || rawUnit === 'min' || rawUnit === 'minutes' || !rawUnit) ? 'minutes' : rawUnit;
                    methodDesc = `Quantity (${unitStr})`;
                }
            } else if (t.check_method === 'scale') {
                methodDesc = isVi ? `Thang đo 1–${t.scale_max || 5}` : `Scale 1–${t.scale_max || 5}`;
            } else if (t.check_method === 'options' || t.check_method === 'yes_no') {
                let optStr = '';
                if (t.options && Array.isArray(t.options) && t.options.length > 0) {
                    optStr = t.options.join(', ');
                } else {
                    const isSleep = (t.name || '').toLowerCase().includes('sleep') || (t.name || '').toLowerCase().includes('giấc ngủ');
                    const defaultOpts = isSleep 
                        ? (isVi ? ['Tốt', 'Chưa tốt'] : ['Good', 'Not good']) 
                        : (isVi ? ['Có', 'Không'] : ['Yes', 'No']);
                    optStr = defaultOpts.join(', ');
                }
                methodDesc = isVi ? `Lựa chọn (${optStr})` : `Options (${optStr})`;
            }

            let catLabel = t.type_label;
            if (!catLabel || catLabel === 'Tracker' || catLabel === 'Mục') {
                catLabel = t.category === 'stress_sign'
                    ? (isVi ? 'Chỉ số căng thẳng' : 'Sign of stress')
                    : (t.category === 'supportive' ? (isVi ? 'Chỉ số hỗ trợ' : 'Supportive') : (isVi ? 'Chung' : 'General'));
            }

            return `
                <div class="p-3.5 sm:p-4 rounded-2xl border ${isKept ? 'border-[#ECC9BA] bg-white/85 shadow-2xs' : 'border-[#ECC9BA]/60 bg-[#93AFBC]/10 opacity-75'} space-y-2.5 transition">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-3">
                            <span class="w-3 h-3 rounded-full inline-block shrink-0" style="background-color: ${dotColor};"></span>
                            <div>
                                <div class="flex items-center space-x-2">
                                    <h4 class="text-xs sm:text-sm font-bold text-[#202124]">${escapeHTML(t.name)}</h4>
                                    <span class="text-[10px] font-bold px-2 py-0.5 rounded-full ${isKept ? 'bg-[#8EA28F]/15 text-[#25422D] border border-[#8EA28F]/40' : 'bg-stone-200/80 text-stone-600'}">
                                        ${isKept ? escapeHTML(activeLabel) : (isVi ? 'Đã ngừng tracking (Lưu trữ)' : 'Stopping (Archived)')}
                                    </span>
                                </div>
                                <span class="text-[11px] text-[#5F5B58]">${escapeHTML(catLabel)} · ${escapeHTML(methodDesc)}</span>
                            </div>
                        </div>

                        <div class="flex items-center space-x-2">
                            ${isKept ? `
                                <button type="button" onclick="window.TempoRecoverySetup.openEditTrackerInAdjustment(${idx}, false)"
                                        class="px-3 py-1.5 rounded-xl text-xs font-semibold text-[#202124] hover:text-[#000] border border-[#93AFBC]/50 bg-white hover:bg-[#93AFBC]/15 transition cursor-pointer shadow-2xs">
                                    ${escapeHTML(editLabel)}
                                </button>
                                <button type="button" onclick="window.TempoRecoverySetup.toggleTrackerKept(${idx})"
                                        class="px-3 py-1.5 rounded-xl text-xs font-semibold text-stone-600 hover:text-stone-900 border border-stone-300/80 bg-white hover:bg-stone-100 transition cursor-pointer shadow-2xs">
                                    ${escapeHTML(stopLabel)}
                                </button>
                            ` : `
                                <button type="button" onclick="window.TempoRecoverySetup.toggleTrackerKept(${idx})"
                                        class="px-3 py-1.5 rounded-xl text-xs font-bold text-[#25422D] hover:bg-[#8EA28F]/20 border border-[#8EA28F]/50 bg-white transition cursor-pointer shadow-2xs">
                                    ${escapeHTML(keepLabel)}
                                </button>
                            `}
                        </div>
                    </div>

                    ${!isKept ? `
                        <p class="text-[11px] text-[#5F5B58] italic">
                            ${isVi ? '✓ Mục này sẽ được chuyển vào lưu trữ. Dữ liệu trước đó vẫn được giữ nguyên.' : '✓ This item will be removed from daily check-ins. Its past check-in records will remain preserved in your archive.'}
                        </p>
                    ` : ''}

                    ${methodChanged ? `
                        <div class="p-2.5 rounded-xl bg-[#93AFBC]/15 border border-[#93AFBC]/40 text-[11px] text-[#2C4857] flex items-center space-x-1.5">
                            <span>⚡</span>
                            <span>${isVi ? 'Cách tracking đã đổi — dữ liệu check-in mới sẽ dùng định dạng mới.' : 'Method changed — new check-ins will use the newly recorded format.'}</span>
                        </div>
                    ` : ''}
                </div>
            `;
        }).join('');

        const newTrackersHTML = adjustmentDraft.newTrackers.map((t, idx) => `
            <div class="p-3.5 sm:p-4 rounded-2xl border-2 border-dashed border-[#8EA28F]/60 bg-[#8EA28F]/10 flex items-center justify-between">
                <div class="flex items-center space-x-3">
                    <span class="w-3 h-3 rounded-full inline-block shrink-0 bg-[#8EA28F]"></span>
                    <div>
                        <div class="flex items-center space-x-2">
                            <h4 class="text-xs sm:text-sm font-bold text-[#25422D]">${escapeHTML(t.name)} ${isVi ? '(Mới)' : '(New)'}</h4>
                            <span class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-[#8EA28F]/20 text-[#25422D] border border-[#8EA28F]/40">${isVi ? 'Sắp thêm' : 'To be added'}</span>
                        </div>
                        <span class="text-[11px] text-[#5F5B58]">${escapeHTML(t.check_method)}</span>
                    </div>
                </div>
                <div class="flex items-center space-x-2">
                    <button type="button" onclick="window.TempoRecoverySetup.openEditTrackerInAdjustment(${idx}, true)"
                            class="px-3 py-1.5 rounded-xl text-xs font-semibold text-[#202124] hover:text-[#000] border border-[#93AFBC]/50 bg-white hover:bg-[#93AFBC]/15 cursor-pointer shadow-2xs">
                        ${escapeHTML(editLabel)}
                    </button>
                    <button type="button" onclick="window.TempoRecoverySetup.removeNewTracker(${idx})"
                            class="text-stone-400 hover:text-red-500 text-xs font-bold px-1.5 cursor-pointer">
                        ✕
                    </button>
                </div>
            </div>
        `).join('');

        container.innerHTML = `
            <div class="space-y-5" data-tempo-ui="rmode-adjust-trackers">
                <div class="flex items-center justify-between text-xs text-[#5F5B58]">
                    <span class="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-[#8EA28F]/15 text-[#25422D] border border-[#8EA28F]/40 font-extrabold uppercase tracking-wider text-[11px]">
                        <span>🌱</span>
                        <span>${escapeHTML(stepBadge)}</span>
                    </span>
                    <span class="font-semibold text-xs text-[#5F5B58]">${escapeHTML(setupAdjustmentLabel)}</span>
                </div>

                <div class="space-y-1">
                    <h3 class="font-heading text-xl sm:text-2xl font-extrabold text-[#202124]">
                        ${escapeHTML(title)}
                    </h3>
                    <p class="text-xs text-[#5F5B58] leading-relaxed">
                        ${escapeHTML(desc)}
                    </p>
                </div>

                <!-- Items list -->
                <div class="space-y-2.5 max-h-[46vh] overflow-y-auto pr-1" data-tempo-section="adjust-items-list">
                    ${trackersListHTML}
                    ${newTrackersHTML}
                </div>

                <!-- Add Button -->
                <div class="pt-1">
                    <button type="button" onclick="window.TempoRecoverySetup.openAddTrackerInAdjustment()"
                            class="px-4 py-2.5 rounded-xl border border-[#93AFBC]/60 hover:border-[#93AFBC] text-xs font-bold text-[#2C4857] transition cursor-pointer flex items-center space-x-1.5 bg-white/90 hover:bg-[#93AFBC]/15 shadow-2xs">
                        <span>${escapeHTML(addLabel)}</span>
                    </button>
                </div>

                <!-- Nav footer -->
                <div class="pt-4 border-t border-[#ECC9BA]/60 flex items-center justify-between">
                    <button type="button" onclick="window.TempoRecoverySetup.handleAdjustBack()"
                            class="px-4 py-2 rounded-xl text-xs font-semibold text-[#5F5B58] hover:text-[#202124] transition cursor-pointer">
                        ${escapeHTML(backLabel)}
                    </button>
                    <button type="button" onclick="window.TempoRecoverySetup.goToStage('adjust_note')"
                            class="btn-primary px-6 py-2.5 rounded-xl font-bold text-xs sm:text-sm shadow-xs inline-flex items-center space-x-2 transition cursor-pointer bg-[#8EA28F] hover:bg-[#7D917E] text-white border border-[#7D917E]/30">
                        <span>${escapeHTML(continueLabel)}</span>
                    </button>
                </div>

            </div>
        `;
    }

    function onAdjustmentMethodSelectChange() {
        const methodSelect = document.getElementById('adjust-edit-method');
        const unitRow = document.getElementById('adjust-edit-unit-row');
        const optsRow = document.getElementById('adjust-edit-options-row');
        const scaleRow = document.getElementById('adjust-edit-scale-row');
        if (!methodSelect) return;

        const val = methodSelect.value;
        if (unitRow) unitRow.classList.toggle('hidden', val !== 'quantity');
        if (optsRow) optsRow.classList.toggle('hidden', val !== 'options' && val !== 'yes_no');
        if (scaleRow) scaleRow.classList.toggle('hidden', val !== 'scale');
    }

    // =========================================================================
    // ADJUSTMENT STAGE 2: RECOVERY NOTE REVIEW
    // =========================================================================

    function renderStageAdjustNote(container) {
        const isVi = isViLocale();
        updateRecoveryCardTheme(true);

        const warningSigns = adjustmentDraft.noteItems.filter(i => i.type === 'warning_sign');
        const helpers = adjustmentDraft.noteItems.filter(i => i.type === 'helper');
        const reminders = adjustmentDraft.noteItems.filter(i => i.type === 'reminder');
        const people = adjustmentDraft.noteItems.filter(i => i.type === 'support_person');

        const stepBadge = isVi ? 'BƯỚC 2/3 · LỜI NHẮN PHỤC HỒI' : 'STEP 2 OF 3 · RECOVERY NOTICE';
        const tagLabel = isVi ? 'Xem lại Lời nhắn phục hồi' : 'Review Recovery Notice';
        const title = isVi ? 'Xem lại Lời nhắn phục hồi' : 'Review your Recovery Notice';
        const desc = isVi
            ? 'Xem lại dấu hiệu cảnh báo, những điều giúp ích, lời nhắc và liên hệ hỗ trợ.'
            : 'Review warning signs, things that help, reminders, and support contacts.';

        const sec1Title = isVi ? 'Khi tôi bắt đầu quá tải' : 'When I start getting overwhelmed';
        const sec2Title = isVi ? 'Những điều giúp ích' : 'Things that seem to help';
        const sec3Title = isVi ? 'Lời nhắc nhở nhẹ nhàng' : 'Gentle reminders';
        const sec4Title = isVi ? 'Người tôi có thể liên hệ' : 'People I can reach out to';

        const addLabel = isVi ? 'Thêm' : 'Add';
        const backBtnLabel = isVi ? 'Quay lại mục tracking' : 'Back to Trackers';
        const reviewBtnLabel = isVi ? 'Xem lại các thay đổi' : 'Review Proposed Changes';

        container.innerHTML = `
            <div class="space-y-5" data-tempo-ui="adjust-recovery-note">
                <div class="flex items-center justify-between text-xs">
                    <span class="font-extrabold uppercase tracking-wider text-[#4F6851] text-[11px]">${escapeHTML(stepBadge)}</span>
                    <span class="text-[#6F6B68] font-medium">${escapeHTML(tagLabel)}</span>
                </div>

                <div class="space-y-1">
                    <h3 class="font-heading text-xl sm:text-2xl font-extrabold text-[#202124]">
                        ${escapeHTML(title)}
                    </h3>
                    <p class="text-xs text-[#6F6B68]">
                        ${escapeHTML(desc)}
                    </p>
                </div>

                <div class="space-y-4 max-h-[46vh] overflow-y-auto pr-1.5 recovery-note-scroll">
                    <!-- SECTION 1: Warning Signs (Warm Blush Accent) -->
                    <div class="p-4 rounded-2xl bg-[#FFF9F4] border border-[#ECC9BA]/80 space-y-3 shadow-2xs transition">
                        <div class="flex items-center justify-between">
                            <div class="flex items-center space-x-2">
                                <span class="w-2.5 h-2.5 rounded-full inline-block bg-[#ECC9BA] shrink-0"></span>
                                <h4 class="text-xs font-bold uppercase tracking-wide text-[#202124]">
                                    1. ${escapeHTML(sec1Title)}
                                </h4>
                            </div>
                            <span class="text-[11px] font-semibold text-[#6F6B68]">(${warningSigns.length})</span>
                        </div>
                        <div class="space-y-1.5">
                            ${warningSigns.length === 0 ? `<p class="text-[11px] text-[#6F6B68] italic py-0.5">${isVi ? 'Chưa có mục nào được lưu.' : 'No items added yet.'}</p>` : ''}
                            ${warningSigns.map((w, idx) => `
                                <div class="flex items-center justify-between px-3.5 py-2 rounded-xl bg-white border border-[#EAE4DF] text-xs text-[#202124] shadow-2xs hover:border-[#ECC9BA] transition">
                                    <span class="font-medium">${escapeHTML(w.text)}</span>
                                    <button type="button" onclick="window.TempoRecoverySetup.removeAdjustmentNoteItem('warning_sign', ${idx})"
                                            class="text-[#6F6B68] hover:text-[#202124] hover:bg-[#ECC9BA]/30 p-1 rounded-lg text-xs transition cursor-pointer ml-2" title="${isVi ? 'Xóa' : 'Remove'}">✕</button>
                                </div>
                            `).join('')}
                        </div>
                        <div class="flex items-center space-x-2 pt-0.5">
                            <input type="text" id="input-adjust-custom-sign" placeholder="${isVi ? '+ Thêm dấu hiệu cảnh báo...' : '+ Add warning sign...'}"
                                   class="flex-1 px-3.5 py-2 rounded-xl border border-[#EAE4DF] text-xs text-[#202124] bg-white placeholder-[#6F6B68]/60 focus:outline-none focus:border-[#8EA28F] focus:ring-1 focus:ring-[#8EA28F]/30 transition shadow-2xs">
                            <button type="button" onclick="window.TempoRecoverySetup.addAdjustmentNoteItem('warning_sign')"
                                    class="px-3.5 py-2 rounded-xl bg-white border border-[#EAE4DF] hover:border-[#8EA28F] text-xs font-bold text-[#202124] hover:bg-[#8EA28F]/10 transition cursor-pointer shadow-2xs flex items-center space-x-1 shrink-0">
                                <span>+</span>
                                <span>${escapeHTML(addLabel)}</span>
                            </button>
                        </div>
                    </div>

                    <!-- SECTION 2: Helpers (Sage Green Accent) -->
                    <div class="p-4 rounded-2xl bg-[#FFF9F4] border border-[#8EA28F]/40 space-y-3 shadow-2xs transition">
                        <div class="flex items-center justify-between">
                            <div class="flex items-center space-x-2">
                                <span class="w-2.5 h-2.5 rounded-full inline-block bg-[#8EA28F] shrink-0"></span>
                                <h4 class="text-xs font-bold uppercase tracking-wide text-[#202124]">
                                    2. ${escapeHTML(sec2Title)}
                                </h4>
                            </div>
                            <span class="text-[11px] font-semibold text-[#6F6B68]">(${helpers.length})</span>
                        </div>
                        <div class="space-y-1.5">
                            ${helpers.length === 0 ? `<p class="text-[11px] text-[#6F6B68] italic py-0.5">${isVi ? 'Chưa có mục nào được lưu.' : 'No items added yet.'}</p>` : ''}
                            ${helpers.map((h, idx) => `
                                <div class="flex items-center justify-between px-3.5 py-2 rounded-xl bg-white border border-[#EAE4DF] text-xs text-[#202124] shadow-2xs hover:border-[#8EA28F]/60 transition">
                                    <span class="font-medium">${escapeHTML(h.text)}</span>
                                    <button type="button" onclick="window.TempoRecoverySetup.removeAdjustmentNoteItem('helper', ${idx})"
                                            class="text-[#6F6B68] hover:text-[#202124] hover:bg-[#8EA28F]/20 p-1 rounded-lg text-xs transition cursor-pointer ml-2" title="${isVi ? 'Xóa' : 'Remove'}">✕</button>
                                </div>
                            `).join('')}
                        </div>
                        <div class="flex items-center space-x-2 pt-0.5">
                            <input type="text" id="input-adjust-custom-helper" placeholder="${isVi ? '+ Thêm điều giúp ích...' : '+ Add helpful thing...'}"
                                   class="flex-1 px-3.5 py-2 rounded-xl border border-[#EAE4DF] text-xs text-[#202124] bg-white placeholder-[#6F6B68]/60 focus:outline-none focus:border-[#8EA28F] focus:ring-1 focus:ring-[#8EA28F]/30 transition shadow-2xs">
                            <button type="button" onclick="window.TempoRecoverySetup.addAdjustmentNoteItem('helper')"
                                    class="px-3.5 py-2 rounded-xl bg-white border border-[#EAE4DF] hover:border-[#8EA28F] text-xs font-bold text-[#202124] hover:bg-[#8EA28F]/10 transition cursor-pointer shadow-2xs flex items-center space-x-1 shrink-0">
                                <span>+</span>
                                <span>${escapeHTML(addLabel)}</span>
                            </button>
                        </div>
                    </div>

                    <!-- SECTION 3: Reminders (Dusty Blue Accent) -->
                    <div class="p-4 rounded-2xl bg-[#FFF9F4] border border-[#93AFBC]/50 space-y-3 shadow-2xs transition">
                        <div class="flex items-center justify-between">
                            <div class="flex items-center space-x-2">
                                <span class="w-2.5 h-2.5 rounded-full inline-block bg-[#93AFBC] shrink-0"></span>
                                <h4 class="text-xs font-bold uppercase tracking-wide text-[#202124]">
                                    3. ${escapeHTML(sec3Title)}
                                </h4>
                            </div>
                            <span class="text-[11px] font-semibold text-[#6F6B68]">(${reminders.length})</span>
                        </div>
                        <div class="space-y-1.5">
                            ${reminders.length === 0 ? `<p class="text-[11px] text-[#6F6B68] italic py-0.5">${isVi ? 'Chưa có mục nào được lưu.' : 'No items added yet.'}</p>` : ''}
                            ${reminders.map((r, idx) => `
                                <div class="flex items-center justify-between px-3.5 py-2 rounded-xl bg-white border border-[#EAE4DF] text-xs text-[#202124] shadow-2xs hover:border-[#93AFBC]/60 transition">
                                    <span class="font-medium italic">"${escapeHTML(r.text)}"</span>
                                    <button type="button" onclick="window.TempoRecoverySetup.removeAdjustmentNoteItem('reminder', ${idx})"
                                            class="text-[#6F6B68] hover:text-[#202124] hover:bg-[#93AFBC]/20 p-1 rounded-lg text-xs transition cursor-pointer ml-2" title="${isVi ? 'Xóa' : 'Remove'}">✕</button>
                                </div>
                            `).join('')}
                        </div>
                        <div class="flex items-center space-x-2 pt-0.5">
                            <input type="text" id="input-adjust-custom-reminder" placeholder="${isVi ? '+ Thêm lời nhắc...' : '+ Add reminder...'}"
                                   class="flex-1 px-3.5 py-2 rounded-xl border border-[#EAE4DF] text-xs text-[#202124] bg-white placeholder-[#6F6B68]/60 focus:outline-none focus:border-[#8EA28F] focus:ring-1 focus:ring-[#8EA28F]/30 transition shadow-2xs">
                            <button type="button" onclick="window.TempoRecoverySetup.addAdjustmentNoteItem('reminder')"
                                    class="px-3.5 py-2 rounded-xl bg-white border border-[#EAE4DF] hover:border-[#8EA28F] text-xs font-bold text-[#202124] hover:bg-[#8EA28F]/10 transition cursor-pointer shadow-2xs flex items-center space-x-1 shrink-0">
                                <span>+</span>
                                <span>${escapeHTML(addLabel)}</span>
                            </button>
                        </div>
                    </div>

                    <!-- SECTION 4: Support People -->
                    <div class="p-4 rounded-2xl bg-[#FFF9F4] border border-[#ECC9BA]/60 space-y-3 shadow-2xs transition">
                        <div class="flex items-center justify-between">
                            <div class="flex items-center space-x-2">
                                <span class="w-2.5 h-2.5 rounded-full inline-block bg-[#ECC9BA] shrink-0"></span>
                                <h4 class="text-xs font-bold uppercase tracking-wide text-[#202124]">
                                    4. ${escapeHTML(sec4Title)}
                                </h4>
                            </div>
                            <span class="text-[11px] font-semibold text-[#6F6B68]">(${people.length})</span>
                        </div>
                        <div class="space-y-1.5">
                            ${people.length === 0 ? `<p class="text-[11px] text-[#6F6B68] italic py-0.5">${isVi ? 'Chưa có người liên hệ nào.' : 'None added yet.'}</p>` : ''}
                            ${people.map((p, idx) => `
                                <div class="flex items-center justify-between px-3.5 py-2 rounded-xl bg-white border border-[#EAE4DF] text-xs text-[#202124] shadow-2xs hover:border-[#ECC9BA] transition">
                                    <span><strong>${escapeHTML(p.text)}</strong> ${p.metadata && p.metadata.relationship ? `<span class="text-[#6F6B68]">(${escapeHTML(p.metadata.relationship)})</span>` : ''}</span>
                                    <button type="button" onclick="window.TempoRecoverySetup.removeAdjustmentNoteItem('support_person', ${idx})"
                                            class="text-[#6F6B68] hover:text-[#202124] hover:bg-[#ECC9BA]/30 p-1 rounded-lg text-xs transition cursor-pointer ml-2" title="${isVi ? 'Xóa' : 'Remove'}">✕</button>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>

                <!-- Nav footer -->
                <div class="pt-4 border-t border-[#ECC9BA]/60 flex items-center justify-between">
                    <button type="button" onclick="window.TempoRecoverySetup.goToStage('adjust_trackers')"
                            class="px-4 py-2.5 rounded-xl text-xs font-bold text-[#6F6B68] hover:text-[#202124] hover:bg-[#ECC9BA]/20 transition cursor-pointer flex items-center space-x-1.5">
                        <span>←</span>
                        <span>${escapeHTML(backBtnLabel)}</span>
                    </button>
                    <button type="button" onclick="window.TempoRecoverySetup.goToStage('adjust_review')"
                            class="btn-primary px-5 py-2.5 rounded-xl font-bold text-xs sm:text-sm shadow-xs inline-flex items-center space-x-2 transition cursor-pointer bg-[#8EA28F] hover:bg-[#7D937E] text-white">
                        <span>${escapeHTML(reviewBtnLabel)}</span>
                        <span>→</span>
                    </button>
                </div>
            </div>
        `;
    }

    function addAdjustmentNoteItem(type) {
        let inputId = '';
        if (type === 'warning_sign') inputId = 'input-adjust-custom-sign';
        else if (type === 'helper') inputId = 'input-adjust-custom-helper';
        else if (type === 'reminder') inputId = 'input-adjust-custom-reminder';

        const input = document.getElementById(inputId);
        if (!input || !input.value.trim()) return;

        adjustmentDraft.noteItems.push({
            type,
            text: input.value.trim(),
            source: 'custom'
        });
        input.value = '';
        renderStageAdjustNote(document.getElementById('recovery-setup-stage-container'));
    }

    function removeAdjustmentNoteItem(type, idxInType) {
        let count = 0;
        for (let i = 0; i < adjustmentDraft.noteItems.length; i++) {
            if (adjustmentDraft.noteItems[i].type === type) {
                if (count === idxInType) {
                    adjustmentDraft.noteItems.splice(i, 1);
                    break;
                }
                count++;
            }
        }
        renderStageAdjustNote(document.getElementById('recovery-setup-stage-container'));
    }

    // =========================================================================
    // ADJUSTMENT STAGE 3: FINAL REVIEW & EXPLICIT CONFIRMATION
    // =========================================================================

    function renderStageAdjustReview(container) {
        const isVi = isViLocale();
        updateRecoveryCardTheme(true);

        const keptTrackers = adjustmentDraft.trackers.filter(t => t.isKept !== false);
        const stoppedTrackers = adjustmentDraft.trackers.filter(t => t.isKept === false);
        const newTrackers = adjustmentDraft.newTrackers;
        const noteItemsCount = adjustmentDraft.noteItems.length;

        const stepBadge = isVi ? 'BƯỚC 3/3 · XÁC NHẬN CUỐI CÙNG' : 'STEP 3 OF 3 · FINAL CONFIRMATION';
        const tagLabel = isVi ? 'Xem lại & xác nhận' : 'Review & Confirm';
        const title = isVi ? 'Xem lại các thay đổi thiết lập' : 'Review proposed setup changes';
        const desc = isVi
            ? 'Vui lòng kiểm tra và xác nhận các thay đổi. Thiết lập chỉ được lưu sau khi bạn xác nhận.'
            : 'Please confirm your updates. Changes will be saved only after explicit confirmation.';

        const activeTrackersHeader = isVi
            ? `CÁC MỤC TRACKING ĐANG HOẠT ĐỘNG (${keptTrackers.length + newTrackers.length})`
            : `ACTIVE TRACKING ITEMS (${keptTrackers.length + newTrackers.length})`;

        const activeLabel = isVi ? 'Đang tracking' : 'Active';
        const newLabel = isVi ? 'Mục mới' : 'New item';
        const stoppedTrackersHeader = isVi
            ? `CÁC MỤC NGỪNG TRACKING (${stoppedTrackers.length})`
            : `ITEMS TO STOP TRACKING (${stoppedTrackers.length})`;
        const stoppedPreservedNote = isVi
            ? '✓ Dữ liệu tracking trước đó vẫn được giữ nguyên an toàn'
            : '✓ Past check-in records safely preserved';

        const recoveryNoticeHeader = isVi ? 'LỜI NHẮN PHỤC HỒI' : 'RECOVERY NOTICE';
        const recoveryNoticeText = noteItemsCount === 0
            ? (isVi ? 'Chưa có nội dung chia sẻ cá nhân nào được lưu.' : '0 personal reflection items saved.')
            : (isVi ? `${noteItemsCount} nội dung chia sẻ cá nhân đã lưu.` : `${noteItemsCount} personal reflection ${noteItemsCount === 1 ? 'item' : 'items'} saved.`);

        const backBtnLabel = isVi ? 'Quay lại chỉnh sửa' : 'Back to Edit';
        const confirmBtnLabel = isVi ? 'Xác nhận & lưu thiết lập ✓' : 'Confirm & Save Setup ✓';

        function getMethodDesc(method, t) {
            if (method === 'percentage') return isVi ? 'Phần trăm (%)' : 'Percentage (%)';
            if (method === 'scale') return isVi ? `Thang đo 1–${t.scale_max || 5}` : `Scale 1–${t.scale_max || 5}`;
            if (method === 'quantity') {
                const unit = t.quantity_unit || (isVi ? 'phút' : 'minutes');
                return isVi ? `Số lượng (${unit})` : `Quantity (${unit})`;
            }
            if (method === 'options' || method === 'yes_no') return isVi ? 'Lựa chọn' : 'Options';
            return method;
        }

        container.innerHTML = `
            <div class="space-y-5" data-tempo-ui="adjust-review-confirm">
                <div class="flex items-center justify-between text-xs">
                    <span class="font-extrabold uppercase tracking-wider text-[#4F6851] text-[11px]">${escapeHTML(stepBadge)}</span>
                    <span class="text-[#6F6B68] font-medium">${escapeHTML(tagLabel)}</span>
                </div>

                <div class="space-y-1">
                    <h3 class="font-heading text-xl sm:text-2xl font-extrabold text-[#202124]">
                        ${escapeHTML(title)}
                    </h3>
                    <p class="text-xs text-[#6F6B68]">
                        ${escapeHTML(desc)}
                    </p>
                </div>

                <div class="space-y-4 max-h-[46vh] overflow-y-auto pr-1.5 recovery-note-scroll text-xs">
                    <!-- Kept Trackers -->
                    <div class="p-4 rounded-2xl bg-[#FFF9F4] border border-[#ECC9BA]/80 space-y-3 shadow-2xs transition">
                        <div class="flex items-center space-x-2">
                            <span class="w-2.5 h-2.5 rounded-full inline-block bg-[#8EA28F] shrink-0"></span>
                            <span class="font-extrabold uppercase tracking-wider text-[#202124] text-[11px] block">
                                ${escapeHTML(activeTrackersHeader)}
                            </span>
                        </div>
                        <div class="space-y-1.5">
                            ${keptTrackers.map(t => {
                                const methodChanged = t.wasEdited && t.check_method !== t.originalMethod;
                                const curMethodLabel = getMethodDesc(t.check_method, t);
                                return `
                                    <div class="flex items-center justify-between p-2.5 rounded-xl bg-white border border-[#EAE4DF] text-xs shadow-2xs">
                                        <div class="flex items-center space-x-2">
                                            <span class="font-bold text-[#202124]">${escapeHTML(t.name)}</span>
                                            <span class="text-[#6F6B68]">(${escapeHTML(curMethodLabel)})</span>
                                        </div>
                                        ${methodChanged ? `
                                            <span class="text-[10px] font-bold text-[#8EA28F] bg-[#8EA28F]/10 px-2.5 py-0.5 rounded-full border border-[#8EA28F]/30">
                                                ${isVi
                                                    ? `Hình thức: ${escapeHTML(getMethodDesc(t.originalMethod, t))} → ${escapeHTML(curMethodLabel)} (áp dụng từ hôm nay)`
                                                    : `Method: ${escapeHTML(t.originalMethod)} → ${escapeHTML(t.check_method)} (effective today)`}
                                            </span>
                                        ` : `<span class="text-[10px] font-bold text-[#25422D] bg-[#8EA28F]/15 border border-[#8EA28F]/40 px-2 py-0.5 rounded-full">${escapeHTML(activeLabel)}</span>`}
                                    </div>
                                `;
                            }).join('')}
                            ${newTrackers.map(t => `
                                <div class="flex items-center justify-between p-2.5 rounded-xl bg-[#FFF9F4] border border-dashed border-[#8EA28F]/60 text-xs shadow-2xs">
                                    <span class="font-bold text-[#4F6851]">${escapeHTML(t.name)} (${escapeHTML(getMethodDesc(t.check_method, t))})</span>
                                    <span class="text-[10px] font-bold text-[#25422D] bg-[#8EA28F]/15 border border-[#8EA28F]/40 px-2 py-0.5 rounded-full">${escapeHTML(newLabel)}</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>

                    <!-- Stopped Trackers -->
                    ${stoppedTrackers.length > 0 ? `
                        <div class="p-4 rounded-2xl bg-[#FFF9F4] border border-[#ECC9BA]/60 space-y-3 shadow-2xs transition">
                            <div class="flex items-center space-x-2">
                                <span class="w-2.5 h-2.5 rounded-full inline-block bg-[#ECC9BA] shrink-0"></span>
                                <span class="font-extrabold uppercase tracking-wider text-[#6F6B68] text-[11px] block">
                                    ${escapeHTML(stoppedTrackersHeader)}
                                </span>
                            </div>
                            <div class="space-y-1.5">
                                ${stoppedTrackers.map(t => `
                                    <div class="p-2.5 rounded-xl bg-white/80 border border-[#EAE4DF] flex items-center justify-between text-xs shadow-2xs">
                                        <span class="font-medium text-[#202124]">${escapeHTML(t.name)}</span>
                                        <span class="text-[11px] text-[#6F6B68]">${escapeHTML(stoppedPreservedNote)}</span>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}

                    <!-- Recovery Notice summary -->
                    <div class="p-4 rounded-2xl bg-[#FFF9F4] border border-[#ECC9BA]/80 space-y-1.5 shadow-2xs transition">
                        <div class="flex items-center space-x-2">
                            <span class="w-2.5 h-2.5 rounded-full inline-block bg-[#93AFBC] shrink-0"></span>
                            <span class="font-extrabold uppercase tracking-wider text-[#202124] text-[11px] block">
                                ${escapeHTML(recoveryNoticeHeader)}
                            </span>
                        </div>
                        <p class="text-xs text-[#6F6B68] pl-4.5">
                            ${escapeHTML(recoveryNoticeText)}
                        </p>
                    </div>
                </div>

                <!-- Footer Nav with Explicit Save Confirmation -->
                <div class="pt-4 border-t border-[#ECC9BA]/60 flex items-center justify-between">
                    <button type="button" onclick="window.TempoRecoverySetup.goToStage('adjust_trackers')"
                            class="px-4 py-2.5 rounded-xl text-xs font-bold text-[#6F6B68] hover:text-[#202124] hover:bg-[#ECC9BA]/20 transition cursor-pointer flex items-center space-x-1.5">
                        <span>←</span>
                        <span>${escapeHTML(backBtnLabel)}</span>
                    </button>
                    <button type="button" onclick="window.TempoRecoverySetup.executeAdjustSetupConfirm()"
                            class="btn-primary px-6 py-2.5 rounded-xl font-bold text-xs sm:text-sm shadow-xs inline-flex items-center space-x-2 transition cursor-pointer bg-[#8EA28F] hover:bg-[#7D937E] text-white">
                        <span>${escapeHTML(confirmBtnLabel)}</span>
                    </button>
                </div>
            </div>
        `;
    }

    function executeAdjustSetupConfirm() {
        try {
            // 1. Process stopped trackers (archive them)
            const stoppedTrackers = adjustmentDraft.trackers.filter(t => t.isKept === false);
            stoppedTrackers.forEach(t => {
                if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.archiveTracker === 'function') {
                    window.TempoRecoverySelfCheck.archiveTracker(t.id);
                }
            });

            // 2. Process edited trackers (update with version bump if method/unit changed)
            const keptTrackers = adjustmentDraft.trackers.filter(t => t.isKept !== false);
            keptTrackers.forEach(t => {
                if (t.wasEdited && window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.updateTracker === 'function') {
                    window.TempoRecoverySelfCheck.updateTracker(t.id, {
                        name: t.name,
                        check_method: t.check_method,
                        quantity_unit: t.quantity_unit,
                        options: t.options,
                        scale_max: t.scale_max,
                        scale_range: t.scale_range,
                        alert_enabled: t.alert_enabled,
                        category: t.category
                    });
                }
            });

            // 3. Process new trackers
            const createdNewIds = [];
            adjustmentDraft.newTrackers.forEach(nt => {
                if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.createTracker === 'function') {
                    const isTension = (nt.name || '').toLowerCase().includes('tension');
                    const created = window.TempoRecoverySelfCheck.createTracker({
                        name: nt.name,
                        check_method: isTension ? 'percentage' : nt.check_method,
                        quantity_unit: nt.quantity_unit,
                        options: nt.options,
                        scale_max: nt.scale_max,
                        scale_range: nt.scale_range,
                        alert_enabled: nt.alert_enabled,
                        category: nt.category || 'stress_sign'
                    });
                    if (created && created.id) createdNewIds.push(created.id);
                }
            });

            // 4. Save Recovery Note items
            if (window.TempoRecoveryNote && typeof window.TempoRecoveryNote.setNoteItems === 'function') {
                window.TempoRecoveryNote.setNoteItems(adjustmentDraft.noteItems);
            }

            // 5. Update active setup record
            const activeTrackerIds = [
                ...keptTrackers.map(t => t.id),
                ...createdNewIds
            ];
            if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.updateActiveSetup === 'function') {
                window.TempoRecoverySelfCheck.updateActiveSetup({ tracker_ids: activeTrackerIds });
            }

            // 6. Complete setup status and close
            markSetupCompleted();
            close();

            // 7. Refresh recovery home and self check workspace
            if (window.TempoMode && typeof window.TempoMode.renderRmodeHome === 'function') {
                window.TempoMode.renderRmodeHome();
            }
            if (window.TempoSelfCheckWorkspace && typeof window.TempoSelfCheckWorkspace.render === 'function') {
                window.TempoSelfCheckWorkspace.render();
            }

            // Case 2 Option B requirement: Navigate to Self-check tool after saving adjustments
            if (window.TempoMode && typeof window.TempoMode.openStrack === 'function') {
                window.TempoMode.openStrack('tool', { sourceContext: 'recovery' });
            }

            if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                const isVi = isViLocale();
                window.TempoApp.showToast(isVi ? "✓ Đã lưu thay đổi hệ thống theo dõi." : "✓ Setup changes saved successfully.");
            }
        } catch (err) {
            console.error("Error confirming setup adjustments:", err);
            if (window.TempoApp && typeof window.TempoApp.showToast === "function") { window.TempoApp.showToast("Failed to save changes. Your active setup has not been altered."); }
        }
    }


    // =========================================================================
    // CASE 1: NEW USER WELCOME MODAL & FLOW
    // =========================================================================

    function renderCase1Welcome(container) {
        const isVi = isViLocale();
        const badge = t('modes.recovery.onboarding.badge', {}, isVi ? 'CHẾ ĐỘ HỒI PHỤC' : 'RECOVERY MODE');
        const title = t('modes.recovery.onboarding.case1Title', {}, isVi ? 'Chào mừng bạn đến với Chế độ Hồi phục' : 'Welcome to Rmode');
        const purpose = t('modes.recovery.onboarding.case1Purpose', {}, isVi ? 'Dành cho bản thân không gian để xả hơi và phục hồi.' : 'Give yourself some space to decompress and recover.');
        const benefits = t('modes.recovery.onboarding.case1Benefits', {}, isVi ? 'Chế độ Hồi phục giúp bạn giảm bớt áp lực, nhận diện những điều hữu ích và tái tạo lại nhịp điệu sinh hoạt bền vững.' : 'Rmode helps you slow down, notice what supports your nervous system, and rebuild a sustainable daily rhythm.');
        const question = t('modes.recovery.onboarding.case1Question', {}, isVi ? 'Bạn đã sẵn sàng thiết lập Hệ thống Theo dõi của mình chưa?' : 'Are you ready to set up your Tracking System?');
        const questionSub = t('modes.recovery.onboarding.case1QuestionSub', {}, isVi ? 'Chọn một vài điều bạn muốn quan sát mỗi ngày. Bạn có thể thay đổi bất cứ lúc nào.' : 'Choose a few things that feel useful to observe. You can adjust them anytime.');
        const btnYes = t('modes.recovery.onboarding.case1Yes', {}, isVi ? 'Có, hãy thiết lập ngay →' : "Yes, let's set it up →");
        const btnLater = t('modes.recovery.onboarding.case1Later', {}, isVi ? 'Để sau' : 'Later');

        container.innerHTML = `
            <div class="space-y-6 text-center py-4" data-tempo-ui="rmode-case1-welcome">
                <div class="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-[#EDF7F1] text-[#166545] border border-[#CDE9DA] text-xs font-extrabold uppercase tracking-wider">
                    <span>🌱</span>
                    <span>${escapeHTML(badge)}</span>
                </div>

                <div class="space-y-3 max-w-lg mx-auto">
                    <h2 class="font-heading text-2xl sm:text-3xl font-extrabold text-[#202124] tracking-tight">
                        ${escapeHTML(title)}
                    </h2>
                    <p class="text-xs sm:text-sm text-[#484541] font-medium leading-relaxed">
                        ${escapeHTML(purpose)}
                    </p>
                    <p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed">
                        ${escapeHTML(benefits)}
                    </p>
                </div>

                <!-- Callout Question Box -->
                <div class="p-4 rounded-2xl bg-[#FBF9F6] border border-[#EAE4DF] max-w-md mx-auto text-center space-y-1.5 shadow-2xs">
                    <span class="text-[11px] font-extrabold uppercase tracking-wider text-[#166545]">
                        ${isVi ? 'HỆ THỐNG THEO DÕI' : 'TRACKING SYSTEM'}
                    </span>
                    <h3 class="font-heading text-sm sm:text-base font-bold text-[#202124]">
                        ${escapeHTML(question)}
                    </h3>
                    <p class="text-xs text-[#6F6B68] leading-relaxed">
                        ${escapeHTML(questionSub)}
                    </p>
                </div>

                <!-- Actions -->
                <div class="pt-2 flex flex-col items-center space-y-3 max-w-xs mx-auto">
                    <button type="button" onclick="window.TempoRecoverySetup.startNewUserSetupFlow()"
                            class="btn-primary w-full px-6 py-3 rounded-xl font-bold text-sm shadow-xs inline-flex items-center justify-center space-x-2 transition cursor-pointer bg-[#166545] hover:bg-[#0E4A32] text-white">
                        <span>${escapeHTML(btnYes)}</span>
                    </button>
                    <button type="button" onclick="window.TempoRecoverySetup.handleCase1Later()"
                            class="text-xs font-semibold text-[#6F6B68] hover:text-[#202124] transition cursor-pointer py-1">
                        ${escapeHTML(btnLater)}
                    </button>
                </div>
            </div>
        `;
    }

    function renderStage1Welcome(container) {
        renderCase1Welcome(container);
    }

    function handleCase1Later() {
        const uid = getUserId();
        // Session guard: suppress duplicate modals during this Rmode session
        sessionStorage.setItem(`tempo_rmode_session_welcomed_${uid}`, 'true');
        // Do NOT mark setup completed. Do NOT create empty tracking system.
        close();
        if (window.TempoMode && typeof window.TempoMode.renderRmodeHome === 'function') {
            window.TempoMode.renderRmodeHome();
        }
    }

    function startNewUserSetupFlow() {
        // Navigate directly to Tracking System configuration (Stage 5)
        goToStage(5);
    }

    function saveNewUserSetupAndGoToSelfCheck() {
        markSetupCompleted();
        close();
        if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
            const isVi = isViLocale();
            window.TempoApp.showToast(isVi ? "✓ Đã thiết lập hệ thống theo dõi." : "✓ Tracking system configured.");
        }
        if (window.TempoMode && typeof window.TempoMode.openStrack === 'function') {
            window.TempoMode.openStrack('tool', { sourceContext: 'recovery' });
        } else if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
            window.TempoApp.navigateTo('stress-check');
        }
    }

    // =========================================================================
    // CASE 2: RETURNING USER WELCOME-BACK MODAL & REVIEW FLOW
    // =========================================================================

    function renderCase2Welcome(container) {
        const isVi = isViLocale();
        const status = checkUserTrackingStatus();
        const count = status.activeCount;

        const badge = t('modes.recovery.onboarding.badgeReturning', {}, isVi ? 'CHẾ ĐỘ HỒI PHỤC · CHÀO MỪNG QUAY LẠI' : 'RECOVERY MODE · WELCOME BACK');
        const title = t('modes.recovery.onboarding.case2Title', {}, isVi ? 'Chào mừng bạn quay lại!' : 'Welcome back!');
        const question = t('modes.recovery.onboarding.case2Question', {}, isVi ? 'Bạn có muốn xem lại Hệ thống tracking của mình không?' : 'Would you like to review your Tracking System?');
        const summary = count > 0
            ? t('modes.recovery.onboarding.case2Summary', { count, s: count === 1 ? '' : 's' }, isVi ? `Bạn hiện có ${count} mục đang tracking.` : `You currently have ${count} active tracking item${count === 1 ? '' : 's'}.`)
            : t('modes.recovery.onboarding.case2SummaryEmpty', {}, isVi ? 'Bạn hiện không có mục tracking nào. Lịch sử tracking trước đây được lưu trữ an toàn trong kho lưu trữ.' : 'You currently have 0 active items. Your past tracking records are safely preserved in archive.');

        const btnYes = t('modes.recovery.onboarding.case2Yes', {}, isVi ? 'Có, xem lại hệ thống →' : 'Yes, review my system →');
        const btnNo = t('modes.recovery.onboarding.case2No', {}, isVi ? 'Không, về Dashboard' : 'No, go to dashboard');
        const trackingStatusLabel = t('modes.recovery.onboarding.case2TrackingStatus', {}, isVi ? 'TRACKING HIỆN TẠI' : 'CURRENT TRACKING');

        // Apply updated palette: soft Warm Blush tint background (not pure-white!), subtle Warm Blush border
        updateRecoveryCardTheme(true);

        container.innerHTML = `
            <div class="space-y-6 text-center py-4" data-tempo-ui="rmode-case2-welcome">
                <div class="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-[#8EA28F] text-white text-xs font-extrabold uppercase tracking-wider shadow-2xs">
                    <span>🌱</span>
                    <span>${escapeHTML(badge)}</span>
                </div>

                <div class="space-y-3 max-w-lg mx-auto">
                    <h2 class="font-heading text-2xl sm:text-3xl font-extrabold text-[#202124] tracking-tight">
                        ${escapeHTML(title)}
                    </h2>
                    <p class="text-sm font-semibold text-[#484541]">
                        ${escapeHTML(question)}
                    </p>
                </div>

                <!-- Active tracking status card: Dusty Blue tint with subtle Warm Blush border -->
                <div class="p-4 sm:p-5 rounded-2xl bg-[#93AFBC]/15 border border-[#ECC9BA] max-w-md mx-auto text-center space-y-1.5 shadow-2xs">
                    <div class="inline-flex items-center space-x-1.5 text-xs font-extrabold uppercase tracking-wider text-[#355B6C]">
                        <span>📊</span>
                        <span>${escapeHTML(trackingStatusLabel)}</span>
                    </div>
                    <p class="text-xs sm:text-sm text-[#374151] leading-relaxed font-medium">
                        ${escapeHTML(summary)}
                    </p>
                </div>

                <!-- Actions -->
                <div class="pt-2 flex flex-col items-center space-y-3 max-w-xs mx-auto">
                    <button type="button" onclick="window.TempoRecoverySetup.openTrackingSystemReview()"
                            class="btn-primary w-full px-6 py-3.5 rounded-xl font-bold text-sm shadow-xs inline-flex items-center justify-center space-x-2 transition cursor-pointer bg-[#8EA28F] hover:bg-[#7D917E] text-white border border-[#7D917E]/30">
                        <span>${escapeHTML(btnYes)}</span>
                    </button>
                    <button type="button" onclick="window.TempoRecoverySetup.handleCase2GoToDashboard()"
                            class="w-full px-5 py-2.5 rounded-xl border border-[#93AFBC]/45 hover:bg-[#93AFBC]/25 text-[#355464] hover:text-[#18313F] text-xs sm:text-sm font-semibold transition cursor-pointer text-center"
                            style="background-color: rgba(147, 175, 188, 0.15);">
                        ${escapeHTML(btnNo)}
                    </button>
                </div>
            </div>
        `;
    }

    function handleCase2GoToDashboard() {
        const uid = getUserId();
        // Session guard: prevent duplicate modals within same Rmode session
        sessionStorage.setItem(`tempo_rmode_session_welcomed_${uid}`, 'true');
        close();
        if (window.TempoMode && typeof window.TempoMode.renderRmodeHome === 'function') {
            window.TempoMode.renderRmodeHome();
        }
    }

    function openTrackingSystemReview() {
        goToStage('case2_review');
    }

    // =========================================================================
    // CASE 2: TRACKING SYSTEM REVIEW INTERFACE
    // =========================================================================

    function renderCase2ReviewSystem(container) {
        const isVi = isViLocale();
        const status = checkUserTrackingStatus();
        const activeTrackers = status.activeTrackers;

        const badge = t('modes.recovery.onboarding.badgeReview', {}, isVi ? 'CHẾ ĐỘ HỒI PHỤC · XEM LẠI HỆ THỐNG TRACKING' : 'RECOVERY MODE · TRACKING SYSTEM REVIEW');
        const title = t('modes.recovery.onboarding.reviewTitle', {}, isVi ? 'Hệ thống tracking của bạn' : 'Your Tracking System');
        const subtitle = t('modes.recovery.onboarding.reviewSubtitle', {}, isVi ? 'Xem lại các mục tracking hiện tại của bạn bên dưới. Bạn có thể giữ nguyên hệ thống hoặc điều chỉnh từng mục.' : 'Review your active tracking items below. You can keep your system as is, or adjust individual items.');

        const optionABtn = t('modes.recovery.onboarding.optionABtn', {}, isVi ? 'Giữ nguyên hệ thống' : 'Keep current system');
        const optionBBtn = t('modes.recovery.onboarding.optionBBtn', {}, isVi ? 'Điều chỉnh hệ thống' : 'Adjust my system');

        const backLabel = t('modes.recovery.onboarding.back', {}, isVi ? '← Quay lại' : '← Back');
        const dashboardLabel = t('modes.recovery.onboarding.backToDashboard', {}, isVi ? 'Quay lại Dashboard' : 'Return to Dashboard');

        // Apply updated palette: soft Warm Blush tint background (not pure-white!), subtle Warm Blush border
        updateRecoveryCardTheme(true);

        // Trackers list HTML
        let itemsListHTML = '';
        if (activeTrackers.length > 0) {
            itemsListHTML = activeTrackers.map(t => {
                const dotColor = t.type_color || (t.category === 'stress_sign' ? '#D48366' : (t.category === 'supportive' ? '#8EA28F' : '#93AFBC'));
                let methodDesc = t.check_method;
                if (t.check_method === 'percentage') methodDesc = isVi ? 'Phần trăm (%)' : 'Percentage (%)';
                else if (t.check_method === 'quantity') methodDesc = `${isVi ? 'Số lượng' : 'Quantity'} (${t.quantity_unit || (isVi ? 'đơn vị' : 'units')})`;
                else if (t.check_method === 'scale') methodDesc = `${isVi ? 'Thang đo' : 'Scale'} 1–${t.scale_max || 5}`;
                else if (t.check_method === 'options' || t.check_method === 'yes_no') {
                    let optStr = '';
                    if (t.options && Array.isArray(t.options) && t.options.length > 0) {
                        optStr = t.options.join(', ');
                    } else {
                        const isSleep = (t.name || '').toLowerCase().includes('sleep') || (t.name || '').toLowerCase().includes('giấc ngủ');
                        const defaultOpts = isSleep 
                            ? (isVi ? ['Tốt', 'Chưa tốt'] : ['Good', 'Not good']) 
                            : (isVi ? ['Có', 'Không'] : ['Yes', 'No']);
                        optStr = defaultOpts.join(', ');
                    }
                    methodDesc = isVi ? `Tùy chọn (${optStr})` : `Options (${optStr})`;
                }

                let catLabel = t.type_label || (t.category === 'stress_sign' ? (isVi ? 'Dấu hiệu căng thẳng' : 'Sign of stress') : (t.category === 'supportive' ? (isVi ? 'Thói quen hỗ trợ' : 'Supportive habit') : (isVi ? 'Chung' : 'General')));

                return `
                    <div class="p-3 sm:p-3.5 rounded-2xl bg-white/80 border border-[#ECC9BA] flex items-center justify-between shadow-2xs transition">
                        <div class="flex items-center space-x-3">
                            <span class="w-3 h-3 rounded-full inline-block shrink-0" style="background-color: ${dotColor};"></span>
                            <div>
                                <h4 class="text-xs sm:text-sm font-bold text-[#202124]">${escapeHTML(t.name)}</h4>
                                <span class="text-[11px] text-[#5F5B58]">${escapeHTML(catLabel)} · ${escapeHTML(methodDesc)}</span>
                            </div>
                        </div>
                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#8EA28F]/15 text-[#25422D] border border-[#8EA28F]/40 shrink-0">
                            ● ${isVi ? 'Đang tracking' : 'Active'}
                        </span>
                    </div>
                `;
            }).join('');
        } else {
            itemsListHTML = `
                <div class="p-5 rounded-2xl bg-white/80 border border-[#ECC9BA] text-center space-y-1">
                    <p class="text-xs font-semibold text-[#202124]">${isVi ? 'Chưa có mục tracking nào đang hoạt động.' : 'No tracking items currently active.'}</p>
                    <p class="text-[11px] text-[#5F5B58]">${isVi ? 'Lịch sử check-in và các mục trước đây trong kho lưu trữ vẫn được bảo toàn an toàn.' : 'Past check-in records and items remain safely preserved in archive.'}</p>
                </div>
            `;
        }

        container.innerHTML = `
            <div class="space-y-5 py-1" data-tempo-ui="rmode-case2-review">
                <!-- Header -->
                <div class="space-y-1.5 text-center max-w-lg mx-auto">
                    <div class="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-[#8EA28F] text-white text-xs font-extrabold uppercase tracking-wider shadow-2xs">
                        <span>🌱</span>
                        <span>${escapeHTML(badge)}</span>
                    </div>
                    <h2 class="font-heading text-xl sm:text-2xl font-extrabold text-[#202124] tracking-tight">
                        ${escapeHTML(title)}
                    </h2>
                    <p class="text-xs sm:text-sm text-[#5F5B58] leading-relaxed">
                        ${escapeHTML(subtitle)}
                    </p>
                </div>

                <!-- Active Trackers List -->
                <div class="space-y-2">
                    <div class="flex items-center justify-between text-xs font-extrabold tracking-wider text-[#355B6C] uppercase">
                        <span>📊 ${escapeHTML(isVi ? `CÁC MỤC TRACKING HIỆN TẠI (${activeTrackers.length})` : `CURRENT TRACKING ITEMS (${activeTrackers.length})`)}</span>
                    </div>
                    <div class="space-y-2 max-h-[36vh] overflow-y-auto pr-1">
                        ${itemsListHTML}
                    </div>
                </div>

                <!-- Two Simplified Actions -->
                <div class="pt-2 flex flex-col sm:flex-row items-center justify-center gap-3">
                    <button type="button" onclick="window.TempoRecoverySetup.executeKeepCurrentSystem()"
                            class="btn-primary w-full sm:flex-1 py-3 px-5 rounded-xl font-bold text-xs sm:text-sm shadow-xs transition cursor-pointer bg-[#8EA28F] hover:bg-[#7D917E] text-white border border-[#7D917E]/30 text-center inline-flex items-center justify-center space-x-1.5">
                        <span>✓</span>
                        <span>${escapeHTML(optionABtn)}</span>
                    </button>
                    <button type="button" onclick="window.TempoRecoverySetup.startAdjustmentFlowFromReview()"
                            class="w-full sm:flex-1 py-3 px-5 rounded-xl border border-[#93AFBC]/45 hover:bg-[#93AFBC]/25 text-[#2D4D5C] hover:text-[#18313F] text-xs sm:text-sm font-semibold transition cursor-pointer text-center inline-flex items-center justify-center space-x-1.5"
                            style="background-color: rgba(147, 175, 188, 0.15);">
                        <span>⚙️</span>
                        <span>${escapeHTML(optionBBtn)}</span>
                    </button>
                </div>

                <!-- Footer Navigation -->
                <div class="pt-3 border-t border-[#ECC9BA]/60 flex items-center justify-between text-xs">
                    <button type="button" onclick="window.TempoRecoverySetup.goToStage('case2_welcome')"
                            class="font-semibold text-[#5F5B58] hover:text-[#202124] transition cursor-pointer">
                        ${escapeHTML(backLabel)}
                    </button>
                    <button type="button" onclick="window.TempoRecoverySetup.handleCase2GoToDashboard()"
                            class="font-semibold text-[#5F5B58] hover:text-[#202124] transition cursor-pointer">
                        ${escapeHTML(dashboardLabel)}
                    </button>
                </div>
            </div>
        `;
    }

    function executeKeepCurrentSystem() {
        const uid = getUserId();
        sessionStorage.setItem(`tempo_rmode_session_welcomed_${uid}`, 'true');
        close();
        if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
            const isVi = isViLocale();
            window.TempoApp.showToast(isVi ? "✓ Đã giữ nguyên hệ thống tracking." : "✓ Current tracking system preserved.");
        }
        if (window.TempoMode && typeof window.TempoMode.openStrack === 'function') {
            window.TempoMode.openStrack('tool', { sourceContext: 'recovery' });
        } else if (window.TempoApp && typeof window.TempoApp.navigateTo === 'function') {
            window.TempoApp.navigateTo('stress-check');
        }
    }

    function startAdjustmentFlowFromReview() {
        startAdjustmentFlow();
    }

    // =========================================================================
    // STAGE 2: LOOKING BACK
    // =========================================================================

    function renderStage2LookingBack(container) {
        container.innerHTML = `
            <div class="space-y-5">
                <div class="flex items-center justify-between text-xs text-[#6F6B68]">
                    <span class="font-bold uppercase tracking-wider text-[#166545]">STEP 1 OF 5 · REFLECTION</span>
                    <span>Looking Back</span>
                </div>

                <div class="space-y-1">
                    <h3 class="font-heading text-xl sm:text-2xl font-extrabold text-[#202124]">What did you notice in yourself?</h3>
                    <p class="text-xs text-[#6F6B68]">
                        Think about the period you've just been through. Choose anything that feels familiar.
                    </p>
                </div>

                <!-- Reflection Chips Grouped -->
                <div class="space-y-4 pt-1">
                    ${LOOKING_BACK_GROUPS.map(g => `
                        <div class="space-y-2">
                            <span class="text-[11px] font-bold uppercase tracking-wider text-stone-500">${g.label}</span>
                            <div class="flex flex-wrap gap-2">
                                ${g.items.map(item => {
                                    const isSelected = setupDraft.lookingBackSelections.includes(item);
                                    return `
                                        <button type="button" onclick="window.TempoRecoverySetup.toggleLookingBack('${escapeHTML(item)}')"
                                                class="px-3.5 py-2 rounded-xl text-xs font-medium transition cursor-pointer border ${isSelected ? 'bg-[#FFE9DC] text-[#B83D08] border-[#FFD2BA] font-bold shadow-xs' : 'bg-white text-[#202124] border-stone-200 hover:border-stone-300'}">
                                            ${isSelected ? '✓ ' : ''}${escapeHTML(item)}
                                        </button>
                                    `;
                                }).join('')}
                            </div>
                        </div>
                    `).join('')}

                    ${setupDraft.lookingBackCustom.length > 0 ? `
                        <div class="space-y-2">
                            <span class="text-[11px] font-bold uppercase tracking-wider text-stone-500">Custom</span>
                            <div class="flex flex-wrap gap-2">
                                ${setupDraft.lookingBackCustom.map(item => `
                                    <button type="button" onclick="window.TempoRecoverySetup.toggleLookingBack('${escapeHTML(item)}')"
                                            class="px-3.5 py-2 rounded-xl text-xs font-bold transition cursor-pointer border bg-[#FFE9DC] text-[#B83D08] border-[#FFD2BA] shadow-xs">
                                        ✓ ${escapeHTML(item)}
                                    </button>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}

                    <!-- Add Custom Input -->
                    <div class="pt-2 flex items-center space-x-2">
                        <input type="text" id="input-custom-looking-back" placeholder="Add something you noticed..."
                               class="flex-1 px-3 py-2 rounded-xl border border-stone-200 text-xs text-[#202124] focus:outline-none focus:border-[#8EA28F]">
                        <button type="button" onclick="window.TempoRecoverySetup.addCustomLookingBack()"
                                class="px-3 py-2 rounded-xl bg-stone-100 hover:bg-stone-200 text-xs font-bold text-[#202124] transition cursor-pointer">
                            + Add
                        </button>
                    </div>
                </div>

                <!-- Footer Nav -->
                <div class="pt-4 border-t border-stone-100 flex items-center justify-between">
                    <button type="button" onclick="window.TempoRecoverySetup.goToStage(1)"
                            class="px-4 py-2 rounded-xl text-xs font-semibold text-stone-500 hover:text-stone-800 transition cursor-pointer">
                        ← Back
                    </button>
                    <button type="button" onclick="window.TempoRecoverySetup.goToStage(3)"
                            class="btn-primary px-5 py-2.5 rounded-xl font-bold text-xs sm:text-sm shadow-xs inline-flex items-center space-x-2 transition cursor-pointer">
                        <span>Continue</span>
                        <span>→</span>
                    </button>
                </div>
            </div>
        `;
    }

    function toggleLookingBack(item) {
        const idx = setupDraft.lookingBackSelections.indexOf(item);
        if (idx === -1) {
            setupDraft.lookingBackSelections.push(item);
        } else {
            setupDraft.lookingBackSelections.splice(idx, 1);
        }
        renderStage2LookingBack(document.getElementById('recovery-setup-stage-container'));
    }

    function addCustomLookingBack() {
        const input = document.getElementById('input-custom-looking-back');
        if (!input || !input.value.trim()) return;
        const text = input.value.trim();
        if (!setupDraft.lookingBackCustom.includes(text)) {
            setupDraft.lookingBackCustom.push(text);
        }
        if (!setupDraft.lookingBackSelections.includes(text)) {
            setupDraft.lookingBackSelections.push(text);
        }
        renderStage2LookingBack(document.getElementById('recovery-setup-stage-container'));
    }

    // =========================================================================
    // STAGE 3: WHAT HELPED
    // =========================================================================

    function renderStage3WhatHelped(container) {
        container.innerHTML = `
            <div class="space-y-5">
                <div class="flex items-center justify-between text-xs text-[#6F6B68]">
                    <span class="font-bold uppercase tracking-wider text-[#166545]">STEP 2 OF 5 · REFLECTION</span>
                    <span>What Helped</span>
                </div>

                <div class="space-y-1">
                    <h3 class="font-heading text-xl sm:text-2xl font-extrabold text-[#202124]">What seemed to make things a little easier?</h3>
                    <p class="text-xs text-[#6F6B68]">
                        Choose anything that felt helpful, even if it only helped a little.
                    </p>
                </div>

                <!-- Reflection Chips Grouped -->
                <div class="space-y-4 pt-1">
                    ${WHAT_HELPED_GROUPS.map(g => `
                        <div class="space-y-2">
                            <span class="text-[11px] font-bold uppercase tracking-wider text-stone-500">${g.label}</span>
                            <div class="flex flex-wrap gap-2">
                                ${g.items.map(item => {
                                    const isSelected = setupDraft.whatHelpedSelections.includes(item);
                                    return `
                                        <button type="button" onclick="window.TempoRecoverySetup.toggleWhatHelped('${escapeHTML(item)}')"
                                                class="px-3.5 py-2 rounded-xl text-xs font-medium transition cursor-pointer border ${isSelected ? 'bg-[#EDF7F1] text-[#166545] border-[#CDE9DA] font-bold shadow-xs' : 'bg-white text-[#202124] border-stone-200 hover:border-stone-300'}">
                                            ${isSelected ? '✓ ' : ''}${escapeHTML(item)}
                                        </button>
                                    `;
                                }).join('')}
                            </div>
                        </div>
                    `).join('')}

                    ${setupDraft.whatHelpedCustom.length > 0 ? `
                        <div class="space-y-2">
                            <span class="text-[11px] font-bold uppercase tracking-wider text-stone-500">Custom</span>
                            <div class="flex flex-wrap gap-2">
                                ${setupDraft.whatHelpedCustom.map(item => `
                                    <button type="button" onclick="window.TempoRecoverySetup.toggleWhatHelped('${escapeHTML(item)}')"
                                            class="px-3.5 py-2 rounded-xl text-xs font-bold transition cursor-pointer border bg-[#EDF7F1] text-[#166545] border-[#CDE9DA] shadow-xs">
                                        ✓ ${escapeHTML(item)}
                                    </button>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}

                    <!-- Add Custom Input -->
                    <div class="pt-2 flex items-center space-x-2">
                        <input type="text" id="input-custom-what-helped" placeholder="Add something that helped you..."
                               class="flex-1 px-3 py-2 rounded-xl border border-stone-200 text-xs text-[#202124] focus:outline-none focus:border-[#8EA28F]">
                        <button type="button" onclick="window.TempoRecoverySetup.addCustomWhatHelped()"
                                class="px-3 py-2 rounded-xl bg-stone-100 hover:bg-stone-200 text-xs font-bold text-[#202124] transition cursor-pointer">
                            + Add
                        </button>
                    </div>
                </div>

                <!-- Footer Nav -->
                <div class="pt-4 border-t border-stone-100 flex items-center justify-between">
                    <button type="button" onclick="window.TempoRecoverySetup.goToStage(2)"
                            class="px-4 py-2 rounded-xl text-xs font-semibold text-stone-500 hover:text-stone-800 transition cursor-pointer">
                        ← Back
                    </button>
                    <button type="button" onclick="window.TempoRecoverySetup.goToStage(4)"
                            class="btn-primary px-5 py-2.5 rounded-xl font-bold text-xs sm:text-sm shadow-xs inline-flex items-center space-x-2 transition cursor-pointer">
                        <span>Continue</span>
                        <span>→</span>
                    </button>
                </div>
            </div>
        `;
    }

    function toggleWhatHelped(item) {
        const idx = setupDraft.whatHelpedSelections.indexOf(item);
        if (idx === -1) {
            setupDraft.whatHelpedSelections.push(item);
        } else {
            setupDraft.whatHelpedSelections.splice(idx, 1);
        }
        renderStage3WhatHelped(document.getElementById('recovery-setup-stage-container'));
    }

    function addCustomWhatHelped() {
        const input = document.getElementById('input-custom-what-helped');
        if (!input || !input.value.trim()) return;
        const text = input.value.trim();
        if (!setupDraft.whatHelpedCustom.includes(text)) {
            setupDraft.whatHelpedCustom.push(text);
        }
        if (!setupDraft.whatHelpedSelections.includes(text)) {
            setupDraft.whatHelpedSelections.push(text);
        }
        renderStage3WhatHelped(document.getElementById('recovery-setup-stage-container'));
    }

    // =========================================================================
    // STAGE 4: RECOVERY NOTE
    // =========================================================================

    function renderStage4RecoveryNote(container) {
        // Suggested warning signs from Looking Back
        const candidateWarningSigns = setupDraft.lookingBackSelections.length > 0
            ? setupDraft.lookingBackSelections
            : ['Trouble focusing', 'Hard to switch off', 'Sleeping later than usual'];

        // Suggested helpers from What Helped
        const candidateHelpers = setupDraft.whatHelpedSelections.length > 0
            ? setupDraft.whatHelpedSelections
            : ['Going outside', 'Taking a real break', 'Drinking water'];

        container.innerHTML = `
            <div class="space-y-5">
                <div class="flex items-center justify-between text-xs text-[#6F6B68]">
                    <span class="font-bold uppercase tracking-wider text-[#FF6B2C]">STEP 3 OF 5 · RECOVERY NOTICE (OPTIONAL)</span>
                    <button type="button" onclick="window.TempoRecoverySetup.goToStage(5)"
                            class="text-xs text-stone-400 hover:text-stone-700 transition cursor-pointer">
                        Skip this step
                    </button>
                </div>

                <div class="space-y-1">
                    <h3 class="font-heading text-xl sm:text-2xl font-extrabold text-[#202124]">Create your Recovery Notice</h3>
                    <p class="text-xs text-[#6F6B68]">
                        Keep a few things you'd like Tempo to remind you of when things feel heavy.
                    </p>
                </div>

                <div class="space-y-5 pt-1">
                    <!-- SECTION 1: WARNING SIGNS (Warm Blush Accent) -->
                    <div class="p-4 rounded-2xl bg-[#FFF9F4] border border-[#ECC9BA]/80 space-y-3 shadow-2xs">
                        <div class="flex items-center space-x-2">
                            <span class="w-2.5 h-2.5 rounded-full inline-block bg-[#ECC9BA] shrink-0"></span>
                            <span class="text-xs font-bold uppercase tracking-wider text-[#202124]">
                                1. When I start getting overwhelmed...
                            </span>
                        </div>
                        <p class="text-[11px] text-stone-500">Suggested from what you noticed:</p>
                        <div class="space-y-1.5" id="note-warning-signs-list">
                            ${candidateWarningSigns.map(item => {
                                const isChecked = setupDraft.noteWarningSigns.includes(item);
                                return `
                                    <label class="flex items-center space-x-2.5 text-xs text-[#202124] cursor-pointer">
                                        <input type="checkbox" onchange="window.TempoRecoverySetup.toggleNoteItem('warning_sign', '${escapeHTML(item)}')"
                                               ${isChecked ? 'checked' : ''} class="rounded text-[#8EA28F] focus:ring-[#8EA28F]">
                                        <span>${escapeHTML(item)}</span>
                                    </label>
                                `;
                            }).join('')}
                        </div>
                        <div class="flex items-center space-x-2 pt-1">
                            <input type="text" id="input-note-custom-sign" placeholder="+ Add my own warning sign..."
                                   class="flex-1 px-3 py-1.5 rounded-xl border border-stone-200 text-xs text-[#202124] focus:outline-none focus:border-[#8EA28F]">
                            <button type="button" onclick="window.TempoRecoverySetup.addCustomNoteItem('warning_sign')"
                                    class="px-3.5 py-1.5 rounded-xl bg-white border border-[#EAE4DF] hover:border-[#8EA28F] text-xs font-bold text-[#202124] hover:bg-[#8EA28F]/10 transition cursor-pointer shadow-2xs">
                                + Add
                            </button>
                        </div>
                    </div>

                    <!-- SECTION 2: HELPERS (Sage Green Accent) -->
                    <div class="p-4 rounded-2xl bg-[#FFF9F4] border border-[#8EA28F]/40 space-y-3 shadow-2xs">
                        <div class="flex items-center space-x-2">
                            <span class="w-2.5 h-2.5 rounded-full inline-block bg-[#8EA28F] shrink-0"></span>
                            <span class="text-xs font-bold uppercase tracking-wider text-[#202124]">
                                2. Things that seem to help...
                            </span>
                        </div>
                        <p class="text-[11px] text-stone-500">Suggested from what helped you:</p>
                        <div class="space-y-1.5" id="note-helpers-list">
                            ${candidateHelpers.map(item => {
                                const isChecked = setupDraft.noteHelpers.includes(item);
                                return `
                                    <label class="flex items-center space-x-2.5 text-xs text-[#202124] cursor-pointer">
                                        <input type="checkbox" onchange="window.TempoRecoverySetup.toggleNoteItem('helper', '${escapeHTML(item)}')"
                                               ${isChecked ? 'checked' : ''} class="rounded text-[#8EA28F] focus:ring-[#8EA28F]">
                                        <span>${escapeHTML(item)}</span>
                                    </label>
                                `;
                            }).join('')}
                        </div>
                        <div class="flex items-center space-x-2 pt-1">
                            <input type="text" id="input-note-custom-helper" placeholder="+ Add my own helpful thing..."
                                   class="flex-1 px-3 py-1.5 rounded-xl border border-stone-200 text-xs text-[#202124] focus:outline-none focus:border-[#8EA28F]">
                            <button type="button" onclick="window.TempoRecoverySetup.addCustomNoteItem('helper')"
                                    class="px-3.5 py-1.5 rounded-xl bg-white border border-[#EAE4DF] hover:border-[#8EA28F] text-xs font-bold text-[#202124] hover:bg-[#8EA28F]/10 transition cursor-pointer shadow-2xs">
                                + Add
                            </button>
                        </div>
                    </div>

                    <!-- SECTION 3: REMINDERS (Dusty Blue Accent) -->
                    <div class="p-4 rounded-2xl bg-[#FFF9F4] border border-[#93AFBC]/50 space-y-3 shadow-2xs">
                        <div class="flex items-center space-x-2">
                            <span class="w-2.5 h-2.5 rounded-full inline-block bg-[#93AFBC] shrink-0"></span>
                            <span class="text-xs font-bold uppercase tracking-wider text-[#202124]">
                                3. What I want to remind myself...
                            </span>
                        </div>
                        <div class="space-y-1.5">
                            ${GENTLE_REMINDER_SUGGESTIONS.map(rem => {
                                const isChecked = setupDraft.noteReminders.includes(rem);
                                return `
                                    <label class="flex items-center space-x-2.5 text-xs text-[#202124] cursor-pointer">
                                        <input type="checkbox" onchange="window.TempoRecoverySetup.toggleNoteItem('reminder', '${escapeHTML(rem)}')"
                                               ${isChecked ? 'checked' : ''} class="rounded text-[#8EA28F] focus:ring-[#8EA28F]">
                                        <span>"${escapeHTML(rem)}"</span>
                                    </label>
                                `;
                            }).join('')}
                        </div>
                        <div class="flex items-center space-x-2 pt-1">
                            <input type="text" id="input-note-custom-reminder" placeholder="+ Write my own reminder..."
                                   class="flex-1 px-3 py-1.5 rounded-xl border border-stone-200 text-xs text-[#202124] focus:outline-none focus:border-[#8EA28F]">
                            <button type="button" onclick="window.TempoRecoverySetup.addCustomNoteItem('reminder')"
                                    class="px-3.5 py-1.5 rounded-xl bg-white border border-[#EAE4DF] hover:border-[#8EA28F] text-xs font-bold text-[#202124] hover:bg-[#8EA28F]/10 transition cursor-pointer shadow-2xs">
                                + Add
                            </button>
                        </div>
                    </div>

                    <!-- SECTION 4: SUPPORT PEOPLE (Warm Blush Accent) -->
                    <div class="p-4 rounded-2xl bg-[#FFF9F4] border border-[#ECC9BA]/60 space-y-3 shadow-2xs">
                        <div class="flex items-center space-x-2">
                            <span class="w-2.5 h-2.5 rounded-full inline-block bg-[#ECC9BA] shrink-0"></span>
                            <span class="text-xs font-bold uppercase tracking-wider text-[#202124]">
                                4. People I can reach out to...
                            </span>
                        </div>
                        <p class="text-[11px] text-stone-500">Add someone you may want to reach out to when things feel like a lot:</p>
                        ${setupDraft.noteSupportPeople.length > 0 ? `
                            <div class="space-y-1">
                                ${setupDraft.noteSupportPeople.map((p, idx) => `
                                    <div class="flex items-center justify-between p-2 rounded-xl bg-white border border-stone-200 text-xs">
                                        <span class="font-bold text-[#202124]">${escapeHTML(p.name)} <span class="text-stone-400 font-normal">(${escapeHTML(p.relationship || 'Support')})</span></span>
                                        <button type="button" onclick="window.TempoRecoverySetup.removeSupportPerson(${idx})" class="text-stone-400 hover:text-red-600 font-bold">✕</button>
                                    </div>
                                `).join('')}
                            </div>
                        ` : ''}
                        <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
                            <input type="text" id="input-setup-person-name" placeholder="Name (e.g. Nhung)"
                                   class="px-3 py-1.5 rounded-xl border border-stone-200 text-xs text-[#202124] focus:outline-none focus:border-[#8EA28F]">
                            <div class="flex items-center space-x-2">
                                <input type="text" id="input-setup-person-rel" placeholder="Relationship (e.g. Friend)"
                                       class="flex-1 px-3 py-1.5 rounded-xl border border-stone-200 text-xs text-[#202124] focus:outline-none focus:border-[#8EA28F]">
                                <button type="button" onclick="window.TempoRecoverySetup.addSupportPersonFromSetup()"
                                        class="px-3 py-1.5 rounded-xl bg-white border border-stone-300 text-xs font-bold text-stone-700 transition cursor-pointer">
                                    + Add
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Footer Nav -->
                <div class="pt-4 border-t border-stone-100 flex items-center justify-between">
                    <button type="button" onclick="window.TempoRecoverySetup.goToStage(3)"
                            class="px-4 py-2 rounded-xl text-xs font-semibold text-stone-500 hover:text-stone-800 transition cursor-pointer">
                        ← Back
                    </button>
                    <div class="flex items-center space-x-3">
                        <button type="button" onclick="window.TempoRecoverySetup.goToStage(5)"
                                class="text-xs font-semibold text-stone-400 hover:text-stone-700 transition cursor-pointer">
                            Skip for now
                        </button>
                        <button type="button" onclick="window.TempoRecoverySetup.saveNoteAndContinue()"
                                class="btn-primary px-5 py-2.5 rounded-xl font-bold text-xs sm:text-sm shadow-xs inline-flex items-center space-x-2 transition cursor-pointer">
                            <span>Continue</span>
                            <span>→</span>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    function toggleNoteItem(type, text) {
        let list;
        if (type === 'warning_sign') list = setupDraft.noteWarningSigns;
        else if (type === 'helper') list = setupDraft.noteHelpers;
        else if (type === 'reminder') list = setupDraft.noteReminders;
        if (!list) return;

        const idx = list.indexOf(text);
        if (idx === -1) list.push(text);
        else list.splice(idx, 1);
    }

    function addCustomNoteItem(type) {
        let inputId, list;
        if (type === 'warning_sign') { inputId = 'input-note-custom-sign'; list = setupDraft.noteWarningSigns; }
        else if (type === 'helper') { inputId = 'input-note-custom-helper'; list = setupDraft.noteHelpers; }
        else if (type === 'reminder') { inputId = 'input-note-custom-reminder'; list = setupDraft.noteReminders; }

        const input = document.getElementById(inputId);
        if (!input || !input.value.trim() || !list) return;

        const val = input.value.trim();
        if (!list.includes(val)) list.push(val);
        input.value = '';
        renderStage4RecoveryNote(document.getElementById('recovery-setup-stage-container'));
    }

    function addSupportPersonFromSetup() {
        const nameInput = document.getElementById('input-setup-person-name');
        const relInput = document.getElementById('input-setup-person-rel');
        if (!nameInput || !nameInput.value.trim()) return;

        setupDraft.noteSupportPeople.push({
            name: nameInput.value.trim(),
            relationship: relInput ? relInput.value.trim() : ''
        });

        nameInput.value = '';
        if (relInput) relInput.value = '';
        renderStage4RecoveryNote(document.getElementById('recovery-setup-stage-container'));
    }

    function removeSupportPerson(idx) {
        setupDraft.noteSupportPeople.splice(idx, 1);
        renderStage4RecoveryNote(document.getElementById('recovery-setup-stage-container'));
    }

    function saveNoteAndContinue() {
        // Collect items into Recovery Note
        if (window.TempoRecoveryNote && typeof window.TempoRecoveryNote.setNoteItems === 'function') {
            const items = [];
            setupDraft.noteWarningSigns.forEach(text => items.push({ type: 'warning_sign', text, source: 'reflection' }));
            setupDraft.noteHelpers.forEach(text => items.push({ type: 'helper', text, source: 'reflection' }));
            setupDraft.noteReminders.forEach(text => items.push({ type: 'reminder', text, source: 'suggestion' }));
            setupDraft.noteSupportPeople.forEach(p => items.push({ type: 'support_person', text: p.name, metadata: { relationship: p.relationship }, source: 'custom' }));

            if (items.length > 0) {
                window.TempoRecoveryNote.setNoteItems(items);
            }
        }
        goToStage(5);
    }

    // =========================================================================
    // STAGE 5: BUILD MY SELF-CHECK (REUSES PHASE 2 TRACKERS)
    // =========================================================================

    // Cache for candidate suggestions in Stage 5 so methods can look up full configuration
    let candidateSuggestionsCache = [];

    function addSuggestedTracker(name) {
        if (!name || typeof name !== 'string') return;
        const trimmed = name.trim();
        if (!trimmed) return;

        if (!window.TempoRecoverySelfCheck || typeof window.TempoRecoverySelfCheck.createTracker !== 'function') return;

        // Check if already active to prevent duplicates
        const activeTrackers = window.TempoRecoverySelfCheck.getActiveTrackers ? window.TempoRecoverySelfCheck.getActiveTrackers() : [];
        const existing = activeTrackers.find(t => t.name.toLowerCase() === trimmed.toLowerCase());
        if (existing) {
            if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                window.TempoApp.showToast(`"${trimmed}" is already in your Self-check.`);
            }
            return;
        }

        // Find suggestion template in cache or standard suggestions
        let tmpl = candidateSuggestionsCache.find(s => s.name.toLowerCase() === trimmed.toLowerCase());
        if (!tmpl) {
            tmpl = {
                name: trimmed,
                category: 'stress_sign',
                check_method: 'yes_no',
                direction: 'higher_concerning',
                pattern_notices_enabled: true
            };
        }

        const payload = {
            name: tmpl.name,
            category: tmpl.category || 'stress_sign',
            check_method: tmpl.check_method || 'yes_no',
            direction: tmpl.direction || (tmpl.category === 'supportive' ? 'higher_better' : 'higher_concerning'),
            quantity_unit: tmpl.quantity_unit || '',
            scale_min: tmpl.scale_min !== undefined ? tmpl.scale_min : 1,
            scale_max: tmpl.scale_max !== undefined ? tmpl.scale_max : 5,
            scale_min_label: tmpl.scale_min_label || 'Very low',
            scale_max_label: tmpl.scale_max_label || 'Very high',
            pattern_notices_enabled: Boolean(tmpl.pattern_notices_enabled)
        };

        const newTracker = window.TempoRecoverySelfCheck.createTracker(payload);
        onTrackerSaved(newTracker);

        if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
            window.TempoApp.showToast(`✓ Added "${tmpl.name}" to Self-check.`);
        }
    }

    function removeTrackerFromSetup(id) {
        if (!window.TempoRecoverySelfCheck || typeof window.TempoRecoverySelfCheck.archiveTracker !== 'function') return;
        window.TempoRecoverySelfCheck.archiveTracker(id);
        onTrackerArchived(id);
    }

    function onTrackerSaved(savedTracker) {
        if (!savedTracker || !savedTracker.id) return;
        if (!setupDraft.selectedTrackerIds) setupDraft.selectedTrackerIds = [];
        if (!setupDraft.selectedTrackerIds.includes(savedTracker.id)) {
            setupDraft.selectedTrackerIds.push(savedTracker.id);
        }
        saveDraftToStorage();

        if (adjustmentDraft && Array.isArray(adjustmentDraft.trackers)) {
            const existingIdx = adjustmentDraft.trackers.findIndex(t => t.id === savedTracker.id);
            if (existingIdx >= 0) {
                adjustmentDraft.trackers[existingIdx] = {
                    ...adjustmentDraft.trackers[existingIdx],
                    ...savedTracker,
                    isKept: true
                };
            } else {
                adjustmentDraft.trackers.push({
                    ...savedTracker,
                    isKept: true,
                    isNew: true,
                    originalMethod: savedTracker.check_method,
                    originalName: savedTracker.name,
                    originalUnit: savedTracker.quantity_unit || '',
                    wasEdited: false
                });
            }
        }

        const container = document.getElementById('recovery-setup-stage-container');
        if (container) {
            if (setupDraft.currentStage === 'adjust_trackers') {
                renderStageAdjustTrackers(container);
            } else if (setupDraft.currentStage === 5) {
                renderStage5BuildSelfCheck(container);
            } else if (setupDraft.currentStage === 6) {
                renderStage6FirstSelfCheck(container);
            }
        }
    }

    function onTrackerArchived(trackerId) {
        if (setupDraft.selectedTrackerIds) {
            setupDraft.selectedTrackerIds = setupDraft.selectedTrackerIds.filter(id => id !== trackerId);
            saveDraftToStorage();
        }
        const container = document.getElementById('recovery-setup-stage-container');
        if (container && setupDraft.currentStage === 5) {
            renderStage5BuildSelfCheck(container);
        }
    }

    function openAddTrackerPrefill(name, category, check_method) {
        if (!name) return;
        const trimmed = name.trim();
        const activeTrackers = (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.getActiveTrackers === 'function')
            ? window.TempoRecoverySelfCheck.getActiveTrackers()
            : [];
        if (activeTrackers.some(t => t.name.toLowerCase() === trimmed.toLowerCase())) {
            if (window.TempoApp && typeof window.TempoApp.showToast === 'function') {
                window.TempoApp.showToast(`"${trimmed}" is already in your Self-check.`);
            }
            return;
        }

        // Add tracker directly using template configuration
        addSuggestedTracker(name);
    }

    function renderStage5BuildSelfCheck(container) {
        const activeTrackers = (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.getActiveTrackers === 'function')
            ? window.TempoRecoverySelfCheck.getActiveTrackers()
            : [];

        // Build candidate suggestions from Stage 2 & Stage 3 reflections and standard suggestions
        candidateSuggestionsCache = [];
        const seenNames = new Set();

        (setupDraft.lookingBackSelections || []).forEach(name => {
            const trimmed = name.trim();
            if (trimmed && !seenNames.has(trimmed.toLowerCase())) {
                seenNames.add(trimmed.toLowerCase());
                const isTension = trimmed.toLowerCase().includes('tension');
                candidateSuggestionsCache.push({
                    name: trimmed,
                    category: 'stress_sign',
                    check_method: isTension ? 'percentage' : 'yes_no',
                    direction: 'higher_concerning',
                    pattern_notices_enabled: true
                });
            }
        });

        (setupDraft.whatHelpedSelections || []).forEach(name => {
            const trimmed = name.trim();
            if (trimmed && !seenNames.has(trimmed.toLowerCase())) {
                seenNames.add(trimmed.toLowerCase());
                candidateSuggestionsCache.push({
                    name: trimmed,
                    category: 'supportive',
                    check_method: 'yes_no',
                    direction: 'higher_better',
                    pattern_notices_enabled: false
                });
            }
        });

        // Add standard helpful suggestions if not already added by reflection
        const standardSuggestions = [
            { name: 'Tension', category: 'stress_sign', check_method: 'percentage', direction: 'higher_concerning', pattern_notices_enabled: true },
            { name: 'Trouble focusing', category: 'stress_sign', check_method: 'yes_no', direction: 'higher_concerning', pattern_notices_enabled: true },
            { name: 'Feeling overwhelmed', category: 'stress_sign', check_method: 'scale', scale_min: 1, scale_max: 5, scale_min_label: 'Low', scale_max_label: 'Very high', direction: 'higher_concerning', pattern_notices_enabled: true },
            { name: 'Sleep quality', category: 'supportive', check_method: 'scale', scale_min: 1, scale_max: 5, scale_min_label: 'Poor', scale_max_label: 'Restful', direction: 'higher_better', pattern_notices_enabled: false },
            { name: 'Took a real break', category: 'supportive', check_method: 'yes_no', direction: 'higher_better', pattern_notices_enabled: false },
            { name: 'Water', category: 'neutral', check_method: 'quantity', quantity_unit: 'glasses', direction: 'higher_better', pattern_notices_enabled: false },
            { name: 'Went outside', category: 'supportive', check_method: 'yes_no', direction: 'higher_better', pattern_notices_enabled: false }
        ];

        standardSuggestions.forEach(s => {
            if (!seenNames.has(s.name.toLowerCase())) {
                seenNames.add(s.name.toLowerCase());
                candidateSuggestionsCache.push(s);
            }
        });

        container.innerHTML = `
            <div class="space-y-5">
                <div class="flex items-center justify-between text-xs text-[#6F6B68]">
                    <span class="font-bold uppercase tracking-wider text-[#166545]">STEP 4 OF 5 · SELF-CHECK</span>
                    <span>Build My Self-check</span>
                </div>

                <div class="space-y-1">
                    <h3 class="font-heading text-xl sm:text-2xl font-extrabold text-[#202124]">
                        ${activeTrackers.length > 0 ? "Your Self-check" : "What would you like to keep track of?"}
                    </h3>
                    <p class="text-xs text-[#6F6B68]">
                        ${activeTrackers.length > 0 ? `You're currently keeping track of ${activeTrackers.length} thing${activeTrackers.length === 1 ? '' : 's'}. You can add more from what you noticed or continue.` : "Choose a few things that feel useful to check in with. Suggested items are completely optional."}
                    </p>
                </div>

                <!-- Existing Active Trackers Display -->
                ${activeTrackers.length > 0 ? `
                    <div class="p-4 rounded-2xl bg-[#EDF7F1]/60 border border-[#CDE9DA] space-y-2.5">
                        <div class="flex items-center justify-between text-xs font-bold text-[#166545]">
                            <span id="setup-active-trackers-count">Active Trackers (${activeTrackers.length})</span>
                            <button type="button" onclick="window.TempoRecoverySelfCheck.openManage()" class="text-xs font-bold underline hover:text-[#0E4A32] cursor-pointer">
                                Manage trackers
                            </button>
                        </div>
                        <div class="flex flex-wrap gap-2 pt-1" id="setup-active-trackers-list">
                            ${activeTrackers.map(t => `
                                <span class="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-white border border-[#CDE9DA] text-xs font-semibold text-[#202124] shadow-2xs">
                                    <span>${t.category === 'stress_sign' ? '🔴' : (t.category === 'supportive' ? '🟢' : '🔵')}</span>
                                    <span>${escapeHTML(t.name)}</span>
                                    <button type="button" onclick="window.TempoRecoverySetup.removeTrackerFromSetup('${t.id}')"
                                            class="text-stone-400 hover:text-red-500 font-bold ml-1 transition cursor-pointer" title="Remove">✕</button>
                                </span>
                            `).join('')}
                        </div>
                    </div>
                ` : `
                    <div class="p-4 rounded-2xl bg-stone-50 border border-stone-200 text-center text-xs text-[#6F6B68]">
                        No trackers added yet. Pick from the suggestions below or add a custom one. (Self-check is optional)
                    </div>
                `}

                <!-- Suggestions to Add -->
                <div class="space-y-2.5 pt-1">
                    <div class="flex items-center justify-between">
                        <span class="text-xs font-extrabold uppercase tracking-wider text-stone-500">
                            Suggested things to track:
                        </span>
                        <span class="text-[11px] text-stone-400">Suggestions are optional</span>
                    </div>
                    <div class="space-y-2 max-h-[36vh] overflow-y-auto pr-1">
                        ${candidateSuggestionsCache.slice(0, 6).map(s => {
                            const isAdded = activeTrackers.some(t => t.name.toLowerCase() === s.name.toLowerCase());
                            return `
                                <div class="p-3 rounded-2xl border ${isAdded ? 'border-[#CDE9DA] bg-[#F7FCF9]' : 'border-stone-200 bg-white'} flex items-center justify-between shadow-2xs transition">
                                    <div class="flex items-center space-x-2.5">
                                        <span class="text-base">${s.category === 'stress_sign' ? '🔴' : (s.category === 'supportive' ? '🟢' : '🔵')}</span>
                                        <div>
                                            <div class="flex items-center space-x-2">
                                                <h4 class="text-xs font-bold text-[#202124]">${escapeHTML(s.name)}</h4>
                                                ${isAdded ? '<span class="text-[10px] font-bold text-[#166545] bg-[#EDF7F1] px-1.5 py-0.5 rounded-full border border-[#CDE9DA]">In Self-check</span>' : ''}
                                            </div>
                                            <span class="text-[10px] text-stone-400">
                                                ${s.category === 'stress_sign' ? 'Sign of stress' : (s.category === 'supportive' ? 'Supportive habit' : 'General')} · ${s.check_method === 'scale' ? 'Scale 1–5' : (s.check_method === 'quantity' ? `Quantity (${s.quantity_unit || 'units'})` : 'Yes / No')}
                                            </span>
                                        </div>
                                    </div>
                                    ${isAdded ? `
                                        <span class="px-3.5 py-1.5 rounded-xl text-xs font-bold bg-[#EDF7F1] text-[#166545] border border-[#CDE9DA] inline-flex items-center space-x-1">
                                            <span>✓ Added</span>
                                        </span>
                                    ` : `
                                        <button type="button" onclick="window.TempoRecoverySetup.addSuggestedTracker('${escapeHTML(s.name)}')"
                                                class="btn-primary px-3.5 py-1.5 rounded-xl text-xs font-bold shadow-xs transition cursor-pointer hover:opacity-95">
                                            + Add
                                        </button>
                                    `}
                                </div>
                            `;
                        }).join('')}
                    </div>
                </div>

                <!-- Custom Add Button -->
                <div class="pt-1 flex items-center space-x-3">
                    <button type="button" onclick="if (window.TempoSelfCheckWorkspace && typeof window.TempoSelfCheckWorkspace.openAddTracking === 'function') { window.TempoSelfCheckWorkspace.openAddTracking(); } else if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.openTrackerModal === 'function') { window.TempoRecoverySelfCheck.openTrackerModal(); }"
                            class="px-4 py-2 rounded-xl border border-stone-300 hover:border-stone-400 text-xs font-bold text-[#202124] transition cursor-pointer flex items-center space-x-1.5">
                        <span>+ Add custom tracker</span>
                    </button>
                </div>

                <!-- Footer Nav -->
                <div class="pt-4 border-t border-stone-100 flex items-center justify-between">
                    <button type="button" onclick="window.TempoRecoverySetup.goToStage(setupDraft.lookingBackSelections.length > 0 ? 4 : 'case1_welcome')"
                            class="px-4 py-2 rounded-xl text-xs font-semibold text-stone-500 hover:text-stone-800 transition cursor-pointer">
                        ← Back
                    </button>
                    <div class="flex items-center space-x-2.5">
                        <button type="button" onclick="window.TempoRecoverySetup.goToStage(6)"
                                class="text-xs font-semibold text-stone-400 hover:text-stone-700 transition cursor-pointer">
                            ${activeTrackers.length === 0 ? 'Skip for now' : 'Continue to First Check-in →'}
                        </button>
                        <button type="button" onclick="window.TempoRecoverySetup.saveNewUserSetupAndGoToSelfCheck()"
                                class="btn-primary px-5 py-2.5 rounded-xl font-bold text-xs sm:text-sm shadow-xs inline-flex items-center space-x-2 transition cursor-pointer bg-[#166545] hover:bg-[#0E4A32] text-white">
                            <span>Save & go to Self-check</span>
                            <span>→</span>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    // =========================================================================
    // STAGE 6: FIRST SELF-CHECK (REUSES PHASE 2 DAILY SELF-CHECK)
    // =========================================================================

    function renderStage6FirstSelfCheck(container) {
        const activeTrackers = (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.getActiveTrackers === 'function')
            ? window.TempoRecoverySelfCheck.getActiveTrackers()
            : [];

        if (activeTrackers.length === 0) {
            // Case: No trackers configured (Valid: zero trackers)
            container.innerHTML = `
                <div class="space-y-6 text-center py-4">
                    <div class="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-stone-100 text-stone-600 border border-stone-200 text-xs font-extrabold uppercase tracking-wider">
                        <span>SELF-CHECK</span>
                    </div>

                    <div class="space-y-2 max-w-md mx-auto">
                        <h3 class="font-heading text-xl sm:text-2xl font-extrabold text-[#202124]">
                            You haven't set anything up to check in with yet.
                        </h3>
                        <p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed">
                            That's completely fine. You can create your Self-check anytime from Recovery Home.
                        </p>
                    </div>

                    <div class="pt-4 flex flex-col sm:flex-row items-center justify-center gap-3">
                        <button type="button" onclick="window.TempoRecoverySetup.goToStage(5)"
                                class="px-4 py-2.5 rounded-xl border border-stone-300 hover:border-stone-400 text-xs font-bold text-[#202124] transition cursor-pointer">
                            + Set up Self-check
                        </button>
                        <button type="button" onclick="window.TempoRecoverySetup.goToStage(7)"
                                class="btn-primary px-6 py-2.5 rounded-xl font-bold text-xs sm:text-sm shadow-xs transition cursor-pointer">
                            Continue →
                        </button>
                    </div>
                </div>
            `;
            return;
        }

        const todayCheckin = window.TempoRecoverySelfCheck.getTodayCheckin();
        if (todayCheckin) {
            // Already checked in today
            const obs = window.TempoRecoverySelfCheck.getObservationsForCheckin(todayCheckin.id);
            const answeredCount = obs.filter(o => o.status === 'answered').length;

            container.innerHTML = `
                <div class="space-y-6 text-center py-4">
                    <div class="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-[#EDF7F1] text-[#166545] border border-[#CDE9DA] text-xs font-bold">
                        <span>✓ Checked in today</span>
                    </div>

                    <div class="space-y-2 max-w-md mx-auto">
                        <h3 class="font-heading text-xl sm:text-2xl font-extrabold text-[#202124]">
                            You've already checked in today
                        </h3>
                        <p class="text-xs sm:text-sm text-[#6F6B68]">
                            You checked in on ${answeredCount} of ${activeTrackers.length} things.
                        </p>
                    </div>

                    <div class="pt-2 flex flex-col sm:flex-row items-center justify-center gap-3">
                        <button type="button" onclick="window.TempoRecoverySelfCheck.openViewToday()"
                                class="px-4 py-2 rounded-xl text-xs font-bold text-[#166545] hover:bg-[#EDF7F1] transition cursor-pointer">
                            View today's check-in
                        </button>
                        <button type="button" onclick="window.TempoRecoverySetup.goToStage(7)"
                                class="btn-primary px-6 py-2.5 rounded-xl font-bold text-xs sm:text-sm shadow-xs transition cursor-pointer">
                            Continue →
                        </button>
                    </div>
                </div>
            `;
            return;
        }

        // Render questionnaire review and check-in launch
        container.innerHTML = `
            <div class="space-y-5">
                <div class="flex items-center justify-between text-xs text-[#6F6B68]">
                    <span class="font-bold uppercase tracking-wider text-[#166545]">STEP 5 OF 5 · FIRST CHECK-IN</span>
                    <button type="button" onclick="window.TempoRecoverySetup.goToStage(7)"
                            class="text-xs text-stone-400 hover:text-stone-700 transition cursor-pointer">
                        Skip for today
                    </button>
                </div>

                <div class="space-y-1">
                    <h3 class="font-heading text-xl sm:text-2xl font-extrabold text-[#202124]">How have things been today?</h3>
                    <p class="text-xs text-[#6F6B68]">Check in with whatever feels useful. You don't have to answer everything.</p>
                </div>

                <!-- Your Active Trackers in Questionnaire -->
                <div class="space-y-2 pt-1">
                    <span class="text-xs font-extrabold uppercase tracking-wider text-stone-500">
                        Things you're checking in on (${activeTrackers.length}):
                    </span>
                    <div class="space-y-2 max-h-[32vh] overflow-y-auto pr-1" id="setup-stage6-trackers-list">
                        ${activeTrackers.map(t => `
                            <div class="p-3.5 rounded-2xl border border-stone-200 bg-white flex items-center justify-between shadow-2xs">
                                <div class="flex items-center space-x-2.5">
                                    <span class="text-base">${t.category === 'stress_sign' ? '🔴' : (t.category === 'supportive' ? '🟢' : '🔵')}</span>
                                    <div>
                                        <h4 class="text-xs font-bold text-[#202124]">${escapeHTML(t.name)}</h4>
                                        <span class="text-[10px] text-stone-400">
                                            ${t.category === 'stress_sign' ? 'Sign of stress' : (t.category === 'supportive' ? 'Supportive habit' : 'General')} · ${t.check_method === 'scale' ? 'Scale 1–5' : (t.check_method === 'quantity' ? `Quantity (${t.quantity_unit || 'units'})` : 'Yes / No')}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>

                <!-- Check-in CTA card -->
                <div class="p-5 text-center rounded-2xl border border-[#CDE9DA] bg-[#EDF7F1]/40 space-y-3">
                    <p class="text-xs text-[#6F6B68]">
                        Your trackers are ready. Start your first daily check-in now:
                    </p>
                    <div class="flex items-center justify-center gap-3">
                        <button type="button" onclick="window.TempoRecoverySetup.launchFirstDailyCheckin()"
                                class="btn-primary px-6 py-2.5 rounded-xl font-bold text-xs sm:text-sm shadow-xs inline-flex items-center space-x-2 transition cursor-pointer">
                            <span>Check in now</span>
                            <span>→</span>
                        </button>
                    </div>
                </div>

                <!-- Footer Nav -->
                <div class="pt-4 border-t border-stone-100 flex items-center justify-between">
                    <button type="button" onclick="window.TempoRecoverySetup.goToStage(5)"
                            class="px-4 py-2 rounded-xl text-xs font-semibold text-stone-500 hover:text-stone-800 transition cursor-pointer">
                        ← Back to trackers
                    </button>
                    <button type="button" onclick="window.TempoRecoverySetup.goToStage(7)"
                            class="px-4 py-2 rounded-xl text-xs font-semibold text-stone-500 hover:text-stone-800 transition cursor-pointer">
                        Skip for today / Continue →
                    </button>
                </div>
            </div>
        `;
    }

    function launchFirstDailyCheckin() {
        if (window.TempoRecoverySelfCheck && typeof window.TempoRecoverySelfCheck.openDailyCheckin === 'function') {
            window.TempoRecoverySelfCheck.openDailyCheckin(false);
            // Advance setup background stage to 7 so when daily checkin finishes, stage 7 is ready!
            goToStage(7);
        }
    }

    // =========================================================================
    // STAGE 7: RECOVERY CHECK-IN COMPLETE + CONTEXTUAL PLAN NEXT STEP
    // =========================================================================

    function renderStage7Complete(container) {
        // Evaluate academic plan context:
        // Case A: Plan exists and has tasks scheduled for today
        // Case B: Plan exists, but no tasks scheduled for today
        // Case C: No plan exists
        const planContext = evaluatePlanContext();

        let planHtml = '';
        if (planContext.type === 'CASE_A') {
            planHtml = `
                <div class="p-4 rounded-2xl bg-white border border-[#FFD2BA] space-y-2 text-left shadow-2xs">
                    <span class="text-[10px] font-extrabold uppercase tracking-wider text-[#B83D08]">WHEN YOU'RE READY</span>
                    <h4 class="font-heading text-sm font-bold text-[#202124]">Your plan for today is still here.</h4>
                    <p class="text-xs text-[#6F6B68]">You have ${planContext.taskCount} planned tasks for today whenever you feel ready to review them.</p>
                    <button type="button" onclick="window.TempoRecoverySetup.viewPlanForToday()"
                            class="text-xs font-bold text-[#B83D08] hover:text-[#9A3412] transition cursor-pointer pt-1 flex items-center space-x-1">
                        <span>View your plan for today</span>
                        <span>→</span>
                    </button>
                </div>
            `;
        } else if (planContext.type === 'CASE_B') {
            planHtml = `
                <div class="p-4 rounded-2xl bg-white border border-stone-200 space-y-2 text-left shadow-2xs">
                    <span class="text-[10px] font-extrabold uppercase tracking-wider text-stone-500">YOUR CURRENT PLAN</span>
                    <h4 class="font-heading text-sm font-bold text-[#202124]">Your existing plan is still here.</h4>
                    <p class="text-xs text-[#6F6B68]">No tasks are scheduled for today. Your existing plan is ready whenever you want to review it.</p>
                    <button type="button" onclick="window.TempoRecoverySetup.viewPlan()"
                            class="text-xs font-bold text-[#166545] hover:text-[#0E4A32] transition cursor-pointer pt-1 flex items-center space-x-1">
                        <span>View your plan</span>
                        <span>→</span>
                    </button>
                </div>
            `;
        } else {
            // Case C: No plan exists
            planHtml = `
                <div class="p-4 rounded-2xl bg-white border border-stone-200 space-y-2 text-left shadow-2xs">
                    <span class="text-[10px] font-extrabold uppercase tracking-wider text-stone-500">WHEN YOU'RE READY</span>
                    <h4 class="font-heading text-sm font-bold text-[#202124]">Need to organize academic deadlines?</h4>
                    <p class="text-xs text-[#6F6B68]">If you have things to work through, Tempo's Urgent Mode can help you make a structured plan.</p>
                    <button type="button" onclick="window.TempoRecoverySetup.promptCreatePlan()"
                            class="text-xs font-bold text-[#FF6B2C] hover:text-[#E05316] transition cursor-pointer pt-1 flex items-center space-x-1">
                        <span>Create your plan</span>
                        <span>→</span>
                    </button>
                </div>
            `;
        }

        container.innerHTML = `
            <div class="space-y-6 text-center py-4">
                <div class="w-12 h-12 rounded-2xl bg-[#EDF7F1] text-[#166545] border border-[#CDE9DA] flex items-center justify-center text-xl font-bold mx-auto shadow-xs">
                    ✓
                </div>

                <div class="space-y-2 max-w-md mx-auto">
                    <span class="text-xs font-extrabold uppercase tracking-wider text-[#166545]">
                        ✓ RECOVERY CHECK-IN COMPLETE
                    </span>
                    <h3 class="font-heading text-2xl font-extrabold text-[#202124]">
                        You've taken some time to slow down.
                    </h3>
                    <p class="text-xs sm:text-sm text-[#6F6B68] leading-relaxed">
                        You looked back, noticed what might help, and set up your personal space. Take things at your own pace from here.
                    </p>
                </div>

                <!-- Primary Action: Return to Recovery Home -->
                <div class="pt-2 max-w-xs mx-auto">
                    <button type="button" onclick="window.TempoRecoverySetup.finishAndReturnHome()"
                            class="btn-primary w-full px-6 py-3 rounded-xl font-bold text-sm shadow-xs inline-flex items-center justify-center space-x-2 transition cursor-pointer">
                        <span>Back to Dashboard</span>
                        <span>→</span>
                    </button>
                </div>

                <!-- Contextual Plan Section -->
                <div class="pt-4 border-t border-stone-100 max-w-md mx-auto">
                    ${planHtml}
                </div>
            </div>
        `;
    }

    function evaluatePlanContext() {
        const storePlan = window.TempoPlanStore && window.TempoPlanStore.getActivePlan
            ? window.TempoPlanStore.getActivePlan('emergency')
            : null;
        const confirmedPlan = (storePlan && storePlan.plannedTasks && storePlan.plannedTasks.length > 0)
            ? storePlan
            : ((window.TempoEmergencyFlow && window.TempoEmergencyFlow.getConfirmedPlan) ? window.TempoEmergencyFlow.getConfirmedPlan() : null);

        if (!confirmedPlan || !confirmedPlan.plannedTasks || confirmedPlan.plannedTasks.length === 0) {
            return { type: 'CASE_C' };
        }

        // Check if there are tasks for today
        const todayStr = (function () {
            const now = new Date();
            return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
        })();

        const todayTasks = confirmedPlan.plannedTasks.filter(pt => pt.day === todayStr && !pt.task?.completed);
        if (todayTasks.length > 0) {
            return { type: 'CASE_A', taskCount: todayTasks.length };
        }

        return { type: 'CASE_B' };
    }

    function finishAndReturnHome() {
        markSetupCompleted();
        close();
        if (window.TempoMode && typeof window.TempoMode.returnToSourceContext === 'function') {
            window.TempoMode.returnToSourceContext();
        } else if (window.TempoMode && typeof window.TempoMode.renderRmodeHome === 'function') {
            window.TempoMode.renderRmodeHome();
        }
    }

    function viewPlanForToday() {
        markSetupCompleted();
        close();
        if (window.TempoPlanWorkspace && typeof window.TempoPlanWorkspace.open === 'function') {
            window.TempoPlanWorkspace.open();
        } else if (window.TempoApp) {
            window.TempoApp.navigateTo('today');
        }
    }

    function viewPlan() {
        markSetupCompleted();
        close();
        if (window.TempoPlanWorkspace && typeof window.TempoPlanWorkspace.open === 'function') {
            window.TempoPlanWorkspace.open();
        } else if (window.TempoApp) {
            window.TempoApp.navigateTo('today');
        }
    }

    function promptCreatePlan() {
        const modal = document.getElementById('modal-recovery-plan-confirm');
        if (modal) modal.classList.remove('hidden');
    }

    function closePlanConfirmModal() {
        const modal = document.getElementById('modal-recovery-plan-confirm');
        if (modal) modal.classList.add('hidden');
    }

    function confirmSwitchToUrgentPlan() {
        closePlanConfirmModal();
        markSetupCompleted();
        close();
        if (window.TempoMode && typeof window.TempoMode.setMode === 'function') {
            window.TempoMode.setMode('emergency');
            if (window.TempoEmergencyFlow && typeof window.TempoEmergencyFlow.openPlanningFlow === 'function') {
                window.TempoEmergencyFlow.openPlanningFlow();
            }
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

    function onDailyCheckinFinished() {
        const modal = document.getElementById('modal-recovery-setup');
        if (modal && !modal.classList.contains('hidden')) {
            goToStage(7);
        }
    }

    function init() {
        ensureModalMounted();
        loadDraftFromStorage();
        try {
            const uid = getUserId();
            const wasOpen = sessionStorage.getItem(`tempo_recovery_setup_open_${uid}`) === 'true';
            if (wasOpen && !isSetupCompleted()) {
                open(setupDraft.currentStage || 1);
            }
        } catch (e) {}
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Register language change listener for instant modal re-render on locale switch
    if (window.TempoI18n && typeof window.TempoI18n.onLanguageChange === 'function') {
        window.TempoI18n.onLanguageChange(() => {
            const modal = document.getElementById('modal-recovery-setup');
            if (modal && !modal.classList.contains('hidden') && setupDraft) {
                goToStage(setupDraft.currentStage || 1);
            }
        });
    }

    window.TempoRecoverySetup = {
        init,
        isViLocale,
        t,
        isIntroSeen,
        markIntroSeen,
        isSetupCompleted,
        hasCompletedRmodeSetup,
        markSetupCompleted,
        resetSetupState,
        checkUserTrackingStatus,
        shouldShowFirstTimeWelcome,
        isReturningUser,
        handleRmodeEntry,
        handleModalClose,
        renderCase1Welcome,
        handleCase1Later,
        startNewUserSetupFlow,
        saveNewUserSetupAndGoToSelfCheck,
        renderCase2Welcome,
        handleCase2GoToDashboard,
        openTrackingSystemReview,
        renderCase2ReviewSystem,
        executeKeepCurrentSystem,
        startAdjustmentFlowFromReview,
        startAdjustmentFlow,
        getAdjustmentDraft: () => adjustmentDraft,
        promptCreateNewSetup,
        confirmCreateNewSetup,
        toggleTrackerKept,
        removeNewTracker,
        openEditTrackerInAdjustment,
        closeTrackerEditInAdjustment,
        handleAdjustBack,
        saveTrackerEditInAdjustment,
        openAddTrackerInAdjustment,
        promptAddNewTrackerInAdjustment,
        onAdjustmentMethodSelectChange,
        addAdjustmentNoteItem,
        removeAdjustmentNoteItem,
        executeAdjustSetupConfirm,
        open,
        close,
        exploreFirst,
        goToStage,
        toggleLookingBack,
        addCustomLookingBack,
        toggleWhatHelped,
        addCustomWhatHelped,
        toggleNoteItem,
        addCustomNoteItem,
        addSupportPersonFromSetup,
        removeSupportPerson,
        saveNoteAndContinue,
        addSuggestedTracker,
        removeTrackerFromSetup,
        onTrackerSaved,
        onTrackerArchived,
        openAddTrackerPrefill,
        launchFirstDailyCheckin,
        onDailyCheckinFinished,
        finishAndReturnHome,
        viewPlanForToday,
        viewPlan,
        promptCreatePlan,
        closePlanConfirmModal,
        confirmSwitchToUrgentPlan
    };

})();
